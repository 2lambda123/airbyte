/*
 * Copyright (c) 2022 Airbyte, Inc., all rights reserved.
 */

package io.airbyte.integrations.destination.mysql;

import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_DB_NAME_OR_USER_ACCESS_DENIED;
import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_HOST_OR_PORT;
import static io.airbyte.integrations.base.errors.utils.ConnectionErrorType.INCORRECT_USERNAME_OR_PASSWORD;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;
import io.airbyte.commons.json.Jsons;
import io.airbyte.db.Database;
import io.airbyte.db.factory.DSLContextFactory;
import io.airbyte.db.factory.DatabaseDriver;
import io.airbyte.integrations.base.JavaBaseConstants;
import io.airbyte.integrations.destination.ExtendedNameTransformer;
import io.airbyte.integrations.standardtest.destination.JdbcDestinationAcceptanceTest;
import io.airbyte.integrations.standardtest.destination.comparator.TestDataComparator;
import io.airbyte.protocol.models.AirbyteCatalog;
import io.airbyte.protocol.models.AirbyteConnectionStatus;
import io.airbyte.protocol.models.AirbyteMessage;
import io.airbyte.protocol.models.AirbyteMessage.Type;
import io.airbyte.protocol.models.AirbyteRecordMessage;
import io.airbyte.protocol.models.AirbyteStateMessage;
import io.airbyte.protocol.models.CatalogHelpers;
import io.airbyte.protocol.models.ConfiguredAirbyteCatalog;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;
import org.jooq.DSLContext;
import org.jooq.SQLDialect;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.MySQLContainer;

public class MySQLDestinationAcceptanceTest extends JdbcDestinationAcceptanceTest {

  protected static final String USERNAME_WITHOUT_PERMISSION = "new_user";
  protected static final String PASSWORD_WITHOUT_PERMISSION = "new_password";

  private MySQLContainer<?> db;
  private final ExtendedNameTransformer namingResolver = new MySQLNameTransformer();

  @Override
  protected String getImageName() {
    return "airbyte/destination-mysql:dev";
  }

  @Override
  protected boolean supportsDBT() {
    return true;
  }

  @Override
  protected boolean implementsNamespaces() {
    return true;
  }

  @Override
  protected boolean supportsNormalization() {
    return true;
  }

  @Override
  protected TestDataComparator getTestDataComparator() {
    return new MySqlTestDataComparator();
  }

  @Override
  protected boolean supportBasicDataTypeTest() {
    return true;
  }

  @Override
  protected boolean supportArrayDataTypeTest() {
    return true;
  }

  @Override
  protected boolean supportObjectDataTypeTest() {
    return true;
  }

  @Override
  protected JsonNode getConfig() {
    return Jsons.jsonNode(ImmutableMap.builder()
        .put("host", db.getHost())
        .put("username", db.getUsername())
        .put("password", db.getPassword())
        .put("database", db.getDatabaseName())
        .put("port", db.getFirstMappedPort())
        .put("ssl", false)
        .build());
  }

  @Override
  protected JsonNode getFailCheckConfig() {
    return Jsons.jsonNode(ImmutableMap.builder()
        .put("host", db.getHost())
        .put("username", db.getUsername())
        .put("password", "wrong password")
        .put("database", db.getDatabaseName())
        .put("port", db.getFirstMappedPort())
        .put("ssl", false)
        .build());
  }

  @Override
  protected String getDefaultSchema(final JsonNode config) {
    if (config.get("database") == null) {
      return null;
    }
    return config.get("database").asText();
  }

  @Override
  protected List<JsonNode> retrieveRecords(final TestDestinationEnv testEnv,
                                           final String streamName,
                                           final String namespace,
                                           final JsonNode streamSchema)
      throws Exception {
    return retrieveRecordsFromTable(namingResolver.getRawTableName(streamName), namespace)
        .stream()
        .map(r -> r.get(JavaBaseConstants.COLUMN_NAME_DATA))
        .collect(Collectors.toList());
  }

  private List<JsonNode> retrieveRecordsFromTable(final String tableName, final String schemaName) throws SQLException {
    try (final DSLContext dslContext = DSLContextFactory.create(
        db.getUsername(),
        db.getPassword(),
        db.getDriverClassName(),
        String.format(DatabaseDriver.MYSQL.getUrlFormatString(),
            db.getHost(),
            db.getFirstMappedPort(),
            db.getDatabaseName()),
        SQLDialect.MYSQL)) {
      return new Database(dslContext).query(
          ctx -> ctx
              .fetch(String.format("SELECT * FROM %s.%s ORDER BY %s ASC;", schemaName, tableName,
                  JavaBaseConstants.COLUMN_NAME_EMITTED_AT))
              .stream()
              .map(this::getJsonFromRecord)
              .collect(Collectors.toList()));
    }
  }

  @Override
  protected List<JsonNode> retrieveNormalizedRecords(final TestDestinationEnv testEnv, final String streamName, final String namespace)
      throws Exception {
    final String tableName = namingResolver.getIdentifier(streamName);
    final String schema = namingResolver.getIdentifier(namespace);
    return retrieveRecordsFromTable(tableName, schema);
  }

  @Override
  protected void setup(final TestDestinationEnv testEnv) {
    db = new MySQLContainer<>("mysql:8.0");
    db.start();
    setLocalInFileToTrue();
    revokeAllPermissions();
    grantCorrectPermissions();
  }

  private void setLocalInFileToTrue() {
    executeQuery("set global local_infile=true");
  }

  private void revokeAllPermissions() {
    executeQuery("REVOKE ALL PRIVILEGES, GRANT OPTION FROM " + db.getUsername() + "@'%';");
  }

  private void grantCorrectPermissions() {
    executeQuery("GRANT ALTER, CREATE, INSERT, SELECT, DROP ON *.* TO " + db.getUsername() + "@'%';");
  }

  private void executeQuery(final String query) {
    try (final DSLContext dslContext = DSLContextFactory.create(
        "root",
        "test",
        db.getDriverClassName(),
        String.format(DatabaseDriver.MYSQL.getUrlFormatString(),
            db.getHost(),
            db.getFirstMappedPort(),
            db.getDatabaseName()),
        SQLDialect.MYSQL)) {
      new Database(dslContext).query(
          ctx -> ctx
              .execute(query));
    } catch (final SQLException e) {
      throw new RuntimeException(e);
    }
  }

  @Override
  protected void tearDown(final TestDestinationEnv testEnv) {
    db.stop();
    db.close();
  }

  @Override
  @Test
  public void testCustomDbtTransformations() throws Exception {
    // We need to create view for testing custom dbt transformations
    executeQuery("GRANT CREATE VIEW ON *.* TO " + db.getUsername() + "@'%';");
    super.testCustomDbtTransformations();
  }

  @Test
  public void testJsonSync() throws Exception {
    final String catalogAsText = "{\n"
        + "  \"streams\": [\n"
        + "    {\n"
        + "      \"name\": \"exchange_rate\",\n"
        + "      \"json_schema\": {\n"
        + "        \"properties\": {\n"
        + "          \"id\": {\n"
        + "            \"type\": \"integer\"\n"
        + "          },\n"
        + "          \"data\": {\n"
        + "            \"type\": \"string\"\n"
        + "          }"
        + "        }\n"
        + "      }\n"
        + "    }\n"
        + "  ]\n"
        + "}\n";

    final AirbyteCatalog catalog = Jsons.deserialize(catalogAsText, AirbyteCatalog.class);
    final ConfiguredAirbyteCatalog configuredCatalog = CatalogHelpers.toDefaultConfiguredCatalog(catalog);
    final List<AirbyteMessage> messages = Lists.newArrayList(
        new AirbyteMessage()
            .withType(Type.RECORD)
            .withRecord(new AirbyteRecordMessage()
                .withStream(catalog.getStreams().get(0).getName())
                .withEmittedAt(Instant.now().toEpochMilli())
                .withData(Jsons.jsonNode(ImmutableMap.builder()
                    .put("id", 1)
                    .put("data", "{\"name\":\"Conferência Faturamento - Custo - Taxas - Margem - Resumo ano inicial até -2\",\"description\":null}")
                    .build()))),
        new AirbyteMessage()
            .withType(Type.STATE)
            .withState(new AirbyteStateMessage().withData(Jsons.jsonNode(ImmutableMap.of("checkpoint", 2)))));

    final JsonNode config = getConfig();
    final String defaultSchema = getDefaultSchema(config);
    runSyncAndVerifyStateOutput(config, messages, configuredCatalog, false);
    retrieveRawRecordsAndAssertSameMessages(catalog, messages, defaultSchema);
  }

  @Override
  @Test
  public void testLineBreakCharacters() {
    // overrides test with a no-op until we handle full UTF-8 in the destination
  }

  protected void assertSameValue(final JsonNode expectedValue, final JsonNode actualValue) {
    if (expectedValue.isBoolean()) {
      // Boolean in MySQL are stored as TINYINT (0 or 1) so we force them to boolean values here
      assertEquals(expectedValue.asBoolean(), actualValue.asBoolean());
    } else {
      assertEquals(expectedValue, actualValue);
    }
  }

  @Test
  void testCheckIncorrectPasswordFailure() {
    JsonNode config = ((ObjectNode) getConfig()).put("password", "fake");
    MySQLDestination destination = new MySQLDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    assertEquals(INCORRECT_USERNAME_OR_PASSWORD.getValue(), actual.getMessage());
  }

  @Test
  public void testCheckIncorrectUsernameFailure() {
    JsonNode config = ((ObjectNode) getConfig()).put("username", "fake");
    MySQLDestination destination = new MySQLDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    assertEquals(INCORRECT_USERNAME_OR_PASSWORD.getValue(), actual.getMessage());
  }

  @Test
  public void testCheckIncorrectHostFailure() {
    JsonNode config = ((ObjectNode) getConfig()).put("host", "localhost2");
    MySQLDestination destination = new MySQLDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    assertEquals(INCORRECT_HOST_OR_PORT.getValue(), actual.getMessage());
  }

  @Test
  public void testCheckIncorrectPortFailure() {
    JsonNode config = ((ObjectNode) getConfig()).put("port", "0000");
    MySQLDestination destination = new MySQLDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    assertEquals(INCORRECT_HOST_OR_PORT.getValue(), actual.getMessage());
  }

  @Test
  public void testCheckIncorrectDataBaseFailure() {
    JsonNode config = ((ObjectNode) getConfig()).put("database", "wrongdatabase");
    MySQLDestination destination = new MySQLDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    assertEquals(INCORRECT_DB_NAME_OR_USER_ACCESS_DENIED.getValue(), actual.getMessage());
  }

  @Test
  public void testUserHasNoPermissionToDataBase() throws SQLException {
    final Connection connection = DriverManager.getConnection(db.getJdbcUrl(), "root", db.getPassword());
    connection.createStatement()
        .execute("create user '" + USERNAME_WITHOUT_PERMISSION + "'@'%' IDENTIFIED BY '" + PASSWORD_WITHOUT_PERMISSION + "';\n");
    JsonNode config = ((ObjectNode) getConfig()).put("username", USERNAME_WITHOUT_PERMISSION);
    ((ObjectNode) config).put("password", PASSWORD_WITHOUT_PERMISSION);
    MySQLDestination destination = new MySQLDestination();
    final AirbyteConnectionStatus actual = destination.check(config);
    assertEquals(AirbyteConnectionStatus.Status.FAILED, actual.getStatus());
    assertEquals(INCORRECT_DB_NAME_OR_USER_ACCESS_DENIED.getValue(), actual.getMessage());
  }

}
