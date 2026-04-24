FROM maven:3.9.6-eclipse-temurin-21-alpine AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
ARG MAVEN_RETRIES=3
RUN set -eux; \
    attempt=1; \
    while [ "${attempt}" -le "${MAVEN_RETRIES}" ]; do \
      mvn -B -ntp clean package -Dspring.profiles.active=docker -DskipTests -Dmaven.wagon.http.retryHandler.count=3 && break; \
      if [ "${attempt}" -eq "${MAVEN_RETRIES}" ]; then \
        echo "Maven build failed after ${MAVEN_RETRIES} attempts"; \
        exit 1; \
      fi; \
      echo "Maven build failed (attempt ${attempt}/${MAVEN_RETRIES}), retrying in 10s..."; \
      attempt=$((attempt + 1)); \
      sleep 10; \
    done

FROM eclipse-temurin:21-jdk
WORKDIR /app
COPY --from=build /build/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
