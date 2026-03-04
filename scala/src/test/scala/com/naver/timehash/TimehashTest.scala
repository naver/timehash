/*
 * Timehash
 * Copyright (c) 2026-present NAVER Corp.
 * Apache-2.0
 */

package com.naver.timehash

import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

class TimehashTest extends AnyFlatSpec with Matchers {
  val th = Timehash()

  "getQueryTerms" should "generate correct keys for 14:30" in {
    val terms = th.getQueryTerms(1430)
    terms should have length 5
    terms(0) should be("12")
    terms(1) should be("1214")
    terms(2) should be("121430")
    terms(3) should be("12143030")
    terms(4) should be("1214303030")
  }

  "getQueryTerms" should "return empty list for invalid input" in {
    val terms = th.getQueryTerms(10001)
    terms should be(empty)
  }

  "getIndexTerms" should "generate keys for simple range (12:00-13:00)" in {
    val terms = th.getIndexTerms("1200", "1300")
    terms should contain("1212")
  }

  "getIndexTerms" should "generate keys for complex range (11:40-21:00)" in {
    val terms = th.getIndexTerms("1140", "2100")
    terms should contain("08113040")
    terms should contain("081145")
    terms should contain("12")
    terms should contain("16")
    terms should contain("2020")
  }

  "query matches index" should "match correctly" in {
    val indexTerms = th.getIndexTerms("1140", "2100")
    
    // Query: 14:30 (should match)
    val queryTerms = th.getQueryTerms(1430)
    val hasMatch = queryTerms.exists(indexTerms.contains)
    hasMatch should be(true)
    
    // Query: 10:00 (should not match)
    val queryTerms10 = th.getQueryTerms(1000)
    val hasMatch10 = queryTerms10.exists(indexTerms.contains)
    hasMatch10 should be(false)
  }
}
