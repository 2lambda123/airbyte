/*
 * Copyright (c) 2021 Airbyte, Inc., all rights reserved.
 */

package io.airbyte.integrations.destination.postgres;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.google.common.collect.ImmutableMap;
import io.airbyte.commons.json.Jsons;
import io.airbyte.db.jdbc.JdbcDatabase;
import io.airbyte.db.jdbc.JdbcUtils;
import io.airbyte.integrations.base.AirbyteMessageConsumer;
import io.airbyte.integrations.base.Destination;
import io.airbyte.protocol.models.AirbyteConnectionStatus;
import io.airbyte.protocol.models.AirbyteMessage;
import io.airbyte.protocol.models.AirbyteMessage.Type;
import io.airbyte.protocol.models.AirbyteRecordMessage;
import io.airbyte.protocol.models.AirbyteStateMessage;
import io.airbyte.protocol.models.CatalogHelpers;
import io.airbyte.protocol.models.ConfiguredAirbyteCatalog;
import io.airbyte.protocol.models.Field;
import io.airbyte.protocol.models.JsonSchemaType;
import io.airbyte.test.utils.PostgreSQLContainerHelper;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;

import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_ACCESS_PERMISSION;
import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_DB_NAME;
import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_HOST_OR_PORT;
import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_USERNAME_OR_PASSWORD;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class PostgresDestinationTest {

  private static PostgreSQLContainer<?> PSQL_DB;

  private static final String USERNAME = "new_user";
  private static final String DATABASE = "new_db";
  private static final String PASSWORD = "new_password";

  private static final String SCHEMA_NAME = "public";
  private static final String STREAM_NAME = "id_and_name";
  private static final ConfiguredAirbyteCatalog CATALOG = new ConfiguredAirbyteCatalog().withStreams(List.of(
      CatalogHelpers.createConfiguredAirbyteStream(
          STREAM_NAME,
          SCHEMA_NAME,
          Field.of("id", JsonSchemaType.NUMBER),
          Field.of("name", JsonSchemaType.STRING))));

  private JsonNode config;

  private static final String EXPECTED_JDBC_URL = "jdbc:postgresql://localhost:1337/db?";

  private JsonNode buildConfigNoJdbcParameters() {
    return Jsons.jsonNode(ImmutableMap.of(
        "host", "localhost",
        "port", 1337,
        "username", "user",
        "database", "db"));
  }

  private JsonNode buildConfigWithExtraJdbcParameters(final String extraParam) {
    return Jsons.jsonNode(ImmutableMap.of(
        "host", "localhost",
        "port", 1337,
        "username", "user",
        "database", "db",
        "jdbc_url_params", extraParam));
  }

  private JsonNode buildConfigNoExtraJdbcParametersWithoutSsl() {
    return Jsons.jsonNode(ImmutableMap.of(
        "host", "localhost",
        "port", 1337,
        "username", "user",
        "database", "db",
        "ssl", false));
  }

  @BeforeAll
  static void init() {
    PSQL_DB = new PostgreSQLContainer<>("postgres:13-alpine");
    PSQL_DB.start();
  }

  @BeforeEach
  void setup() {
    config = PostgreSQLContainerHelper.createDatabaseWithRandomNameAndGetPostgresConfig(PSQL_DB);
  }

  @AfterAll
  static void cleanUp() {
    PSQL_DB.close();
  }

  @Test
  void testJdbcUrlAndConfigNoExtraParams() {
    final JsonNode jdbcConfig = new PostgresDestination().toJdbcConfig(buildConfigNoJdbcParameters());
    assertEquals(EXPECTED_JDBC_URL, jdbcConfig.get("jdbc_url").asText());
  }

  @Test
  void testJdbcUrlEmptyExtraParams() {
    final JsonNode jdbcConfig = new PostgresDestination().toJdbcConfig(buildConfigWithExtraJdbcParameters(""));
    assertEquals(EXPECTED_JDBC_URL, jdbcConfig.get("jdbc_url").asText());
  }

  @Test
  void testJdbcUrlExtraParams() {
    final String extraParam = "key1=value1&key2=value2&key3=value3";
    final JsonNode jdbcConfig = new PostgresDestination().toJdbcConfig(buildConfigWithExtraJdbcParameters(extraParam));
    assertEquals(EXPECTED_JDBC_URL, jdbcConfig.get("jdbc_url").asText());
  }

  @Test
  void testDefaultParamsNoSSL() {
    final Map<String, String> defaultProperties = new PostgresDestination().getDefaultConnectionProperties(
        buildConfigNoExtraJdbcParametersWithoutSsl());
    assertEquals(new HashMap<>(), defaultProperties);
  }

  @Test
  void testDefaultParamsWithSSL() {
    final Map<String, String> defaultProperties = new PostgresDestination().getDefaultConnectionProperties(
        buildConfigNoJdbcParameters());
    assertEquals(PostgresDestination.SSL_JDBC_PARAMETERS, defaultProperties);
  }

  @Test
  void testCheckIncorrectPasswordFailure() {
    var config = buildConfigNoJdbcParameters();
    ((ObjectNode) config).put("password", "fake");
    var destination = new PostgresDestination();
    var actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus(), INCORRECT_USERNAME_OR_PASSWORD.getValue());
  }

  @Test
  public void testCheckIncorrectUsernameFailure() {
    var config = buildConfigNoJdbcParameters();
    ((ObjectNode) config).put("username", "");
    var destination = new PostgresDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus(), INCORRECT_USERNAME_OR_PASSWORD.getValue());
  }

  @Test
  public void testCheckIncorrectHostFailure() {
    var config = buildConfigNoJdbcParameters();
    ((ObjectNode) config).put("host", "localhost2");
    var destination = new PostgresDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus(), INCORRECT_HOST_OR_PORT.getValue());
  }

  @Test
  public void testCheckIncorrectPortFailure() {
    var config = buildConfigNoJdbcParameters();
    ((ObjectNode) config).put("port", "0000");
    var destination = new PostgresDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus(), INCORRECT_HOST_OR_PORT.getValue());
  }

  @Test
  public void testCheckIncorrectDataBaseFailure() {
    var config = buildConfigNoJdbcParameters();
    ((ObjectNode) config).put("database", "wrongdatabase");
    var destination = new PostgresDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus(), INCORRECT_DB_NAME.getValue());
  }

  @Test
  public void testUserHasNoPermissionToDataBase() throws Exception {
    final JdbcDatabase database = PostgreSQLContainerHelper.getJdbcDatabaseFromConfig(PostgreSQLContainerHelper.getDataSourceFromConfig(config));

    database.execute(connection -> connection.createStatement()
            .execute(String.format("create user %s with password '%s';", USERNAME, PASSWORD )));
    database.execute(connection -> connection.createStatement()
            .execute(String.format("create database %s;", DATABASE)));
    // deny access for database for all users from group public
    database.execute(connection -> connection.createStatement()
            .execute(String.format("revoke all on database %s from public;", DATABASE)));

    ((ObjectNode) config).put("username", USERNAME);
    ((ObjectNode) config).put("password", PASSWORD);
    ((ObjectNode) config).put("database", DATABASE);

    var destination = new PostgresDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    Assertions.assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    Assertions.assertEquals(INCORRECT_ACCESS_PERMISSION.getValue(), actual.getMessage());
  }

  // This test is a bit redundant with PostgresIntegrationTest. It makes it easy to run the
  // destination in the same process as the test allowing us to put breakpoint in, which is handy for
  // debugging (especially since we use postgres as a guinea pig for most features).
  @Test
  void sanityTest() throws Exception {
    final Destination destination = new PostgresDestination();
    final AirbyteMessageConsumer consumer = destination.getConsumer(config, CATALOG, Destination::defaultOutputRecordCollector);
    final List<AirbyteMessage> expectedRecords = getNRecords(10);

    consumer.start();
    expectedRecords.forEach(m -> {
      try {
        consumer.accept(m);
      } catch (final Exception e) {
        throw new RuntimeException(e);
      }
    });
    consumer.accept(new AirbyteMessage()
        .withType(Type.STATE)
        .withState(new AirbyteStateMessage().withData(Jsons.jsonNode(ImmutableMap.of(SCHEMA_NAME + "." + STREAM_NAME, 10)))));
    consumer.close();

    final JdbcDatabase database = PostgreSQLContainerHelper.getJdbcDatabaseFromConfig(PostgreSQLContainerHelper.getDataSourceFromConfig(config));

    final List<JsonNode> actualRecords = database.bufferedResultSetQuery(
        connection -> connection.createStatement().executeQuery("SELECT * FROM public._airbyte_raw_id_and_name;"),
        JdbcUtils.getDefaultSourceOperations()::rowToJson);

    assertEquals(
        expectedRecords.stream().map(AirbyteMessage::getRecord).map(AirbyteRecordMessage::getData).collect(Collectors.toList()),
        actualRecords.stream().map(o -> o.get("_airbyte_data").asText()).map(Jsons::deserialize).collect(Collectors.toList()));
  }

  private List<AirbyteMessage> getNRecords(final int n) {
    return IntStream.range(0, n)
        .boxed()
        .map(i -> new AirbyteMessage()
            .withType(Type.RECORD)
            .withRecord(new AirbyteRecordMessage()
                .withStream(STREAM_NAME)
                .withNamespace(SCHEMA_NAME)
                .withEmittedAt(Instant.now().toEpochMilli())
                .withData(Jsons.jsonNode(ImmutableMap.of("id", i, "name", "human " + i)))))
        .collect(Collectors.toList());
  }

}
