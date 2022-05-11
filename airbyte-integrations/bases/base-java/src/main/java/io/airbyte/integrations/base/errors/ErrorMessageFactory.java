/*
 * Copyright (c) 2021 Airbyte, Inc., all rights reserved.
 */

package io.airbyte.integrations.base.errors;

import static io.airbyte.integrations.base.errors.utils.ConnectorType.GCS;
import static io.airbyte.integrations.base.errors.utils.ConnectorType.MONGO;
import static io.airbyte.integrations.base.errors.utils.ConnectorType.MSSQL;
import static io.airbyte.integrations.base.errors.utils.ConnectorType.MYSQL;
import static io.airbyte.integrations.base.errors.utils.ConnectorType.POSTGRES;
import static io.airbyte.integrations.base.errors.utils.ConnectorType.REDSHIFT;
import static io.airbyte.integrations.base.errors.utils.ConnectorType.SNOWFLAKE;

import io.airbyte.integrations.base.errors.messages.DefaultErrorMessage;
import io.airbyte.integrations.base.errors.messages.ErrorMessage;
import io.airbyte.integrations.base.errors.messages.GCSErrorMessage;
import io.airbyte.integrations.base.errors.messages.MongoDbErrorMessage;
import io.airbyte.integrations.base.errors.messages.MssqlErrorMessage;
import io.airbyte.integrations.base.errors.messages.MysqlErrorMessage;
import io.airbyte.integrations.base.errors.messages.PostgresErrorMessage;
import io.airbyte.integrations.base.errors.messages.RedshiftErrorMessage;
import io.airbyte.integrations.base.errors.messages.SnowflakeErrorMessage;
import io.airbyte.integrations.base.errors.utils.ConnectorType;
import java.util.Map;

public class ErrorMessageFactory {

  private final static Map<ConnectorType, ErrorMessage> MAP = Map.of(MSSQL, new MssqlErrorMessage(),
      MYSQL, new MysqlErrorMessage(),
      POSTGRES, new PostgresErrorMessage(),
      MONGO, new MongoDbErrorMessage(),
      REDSHIFT, new RedshiftErrorMessage(),
      GCS, new GCSErrorMessage(),
      SNOWFLAKE, new SnowflakeErrorMessage(),
      ConnectorType.DEFAULT, new DefaultErrorMessage());

  public static ErrorMessage getErrorMessage(ConnectorType type) {
    if (MAP.containsKey(type)) {
      return MAP.get(type);
    }
    return MAP.get(ConnectorType.DEFAULT);
  }

}
