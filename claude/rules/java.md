# Java Library Installation

When adding Java dependencies (Maven/Gradle):

1. Always check latest version first using Maven Central search
2. Then add with the verified latest version

## Version Check Methods

### Maven Central API (Recommended)
```bash
# Search for latest version
curl -s "https://search.maven.org/solrsearch/select?q=g:<groupId>%20AND%20a:<artifactId>&rows=1&wt=json" | jq -r '.response.docs[0].latestVersion'

# Example: Spring Boot
curl -s "https://search.maven.org/solrsearch/select?q=g:org.springframework.boot%20AND%20a:spring-boot-starter&rows=1&wt=json" | jq -r '.response.docs[0].latestVersion'

# Example: Lombok
curl -s "https://search.maven.org/solrsearch/select?q=g:org.projectlombok%20AND%20a:lombok&rows=1&wt=json" | jq -r '.response.docs[0].latestVersion'
```

### Maven Command
```bash
# Display available updates for dependencies
mvn versions:display-dependency-updates

# Display available plugin updates
mvn versions:display-plugin-updates
```

### Gradle Command
```bash
# Requires ben-manes/gradle-versions-plugin
./gradlew dependencyUpdates
```

## Common Dependencies Quick Reference

| Library | GroupId | ArtifactId |
|---------|---------|------------|
| Spring Boot | org.springframework.boot | spring-boot-starter |
| Spring Web | org.springframework.boot | spring-boot-starter-web |
| Lombok | org.projectlombok | lombok |
| Jackson | com.fasterxml.jackson.core | jackson-databind |
| Guava | com.google.guava | guava |
| JUnit 5 | org.junit.jupiter | junit-jupiter |
| Mockito | org.mockito | mockito-core |
| SLF4J | org.slf4j | slf4j-api |
| Logback | ch.qos.logback | logback-classic |

This ensures:
- Installing up-to-date packages
- Avoiding outdated cached versions
- Explicit version awareness before installation
