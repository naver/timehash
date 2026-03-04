name := "timehash"
version := "0.1.0"
scalaVersion := "2.13.12"

organization := "com.naver"
description := "Hierarchical time indexing for efficient business hours search"

libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.17" % Test

scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-unchecked"
)

// Example
lazy val example = project
  .settings(
    mainClass in (Compile, run) := Some("com.naver.timehash.example.BasicUsage")
  )
