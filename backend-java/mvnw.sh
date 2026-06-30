#!/bin/sh
MAVEN_OPTS="-Xmx512m"
exec mvnw "$@"
