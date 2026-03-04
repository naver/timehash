plugins {
    kotlin("jvm") version "1.9.0"
    `java-library`
}

group = "com.naver"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation(kotlin("stdlib"))
    testImplementation("junit:junit:4.13.2")
}

tasks.test {
    useJUnit()
}

tasks.jar {
    archiveBaseName.set("timehash")
}
