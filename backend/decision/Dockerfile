FROM maven:3.9.6-eclipse-temurin-21-alpine AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn clean package -Dspring.profiles.active=docker -DskipTests

FROM eclipse-temurin:21-jdk
WORKDIR /app
COPY --from=build /build/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
