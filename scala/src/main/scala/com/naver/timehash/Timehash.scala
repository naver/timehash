/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash

/**
 * Timehash: Hierarchical time indexing for efficient business hours search.
 *
 * Timehash generates hierarchical hash keys for time ranges, enabling efficient
 * temporal filtering in search systems with minimal index overhead.
 */
class Timehash(private val measures: List[Int] = Timehash.DefaultMeasures) {
  /**
   * Generate query terms for a given time.
   *
   * @param hhmm Time in hhmm format (e.g., 1720 for 17:20)
   * @return List of hierarchical hash keys for the query time
   */
  def getQueryTerms(hhmm: Int): List[String] = {
    if (hhmm > 10000) {
      return List.empty
    }

    measures.foldLeft(List.empty[String]) { (terms, measure) =>
      val (target, measureVal) = if (measure >= 100) {
        (hhmm / 100, measure / 100)
      } else {
        (hhmm % 100, measure)
      }

      val key = (target / measureVal) * measureVal
      val term = twoDigitTerm(key)

      if (terms.isEmpty) {
        List(term)
      } else {
        terms :+ (terms.last + term)
      }
    }
  }

  /**
   * Generate index terms for a time range.
   *
   * @param fromTime Start time in hhmm format (e.g., "1140")
   * @param toTime End time in hhmm format (e.g., "2100")
   * @return List of hierarchical hash keys covering the time range
   */
  def getIndexTerms(fromTime: String, toTime: String): List[String] = {
    val fromInt = fromTime.toIntOption.getOrElse(0)
    val toInt = toTime.toIntOption.getOrElse(0)
    val terms = scala.collection.mutable.ListBuffer.empty[String]
    cover(terms, 0, "", fromInt, toInt)
    terms.toList
  }

  private def twoDigitTerm(key: Int): String = {
    val k = if (key >= 100) key / 100 else key
    s"${k / 10}${k % 10}"
  }

  private def cover(
    terms: scala.collection.mutable.ListBuffer[String],
    measureIndex: Int,
    parentKey: String,
    from: Int,
    to: Int
  ): Unit = {
    if (measureIndex >= measures.length) {
      return
    }

    val measure = measures(measureIndex)
    var fromVal = from
    var toVal = to

    if (measure < 100) {
      fromVal %= 100
      toVal %= 100
      if (toVal == 0) {
        toVal = 60
      }
    }

    val start = fromVal / measure
    val end = toVal / measure

    for (i <- start to end) {
      val key = measure * i

      if (fromVal <= key && key + measure <= toVal) {
        val term = twoDigitTerm(key)
        terms += (parentKey + term)
      } else if (key < fromVal && fromVal < key + measure) {
        val term = twoDigitTerm(key)
        val end = math.min(key + measure, toVal)
        cover(terms, measureIndex + 1, parentKey + term, fromVal, end)
      } else if (key < toVal && toVal < key + measure) {
        val term = twoDigitTerm(key)
        cover(terms, measureIndex + 1, parentKey + term, key, toVal)
      }
    }
  }
}

object Timehash {
  /**
   * Default measures: [400, 100, 15, 5, 1] representing:
   * - 400 minutes (4 hours)
   * - 100 minutes (1 hour, treated as 60 minutes)
   * - 15 minutes
   * - 5 minutes
   * - 1 minute
   */
  val DefaultMeasures: List[Int] = List(400, 100, 15, 5, 1)

  /**
   * Create a new Timehash instance with default measures.
   */
  def apply(): Timehash = new Timehash()

  /**
   * Create a new Timehash instance with custom measures.
   */
  def apply(measures: List[Int]): Timehash = new Timehash(measures)
}
