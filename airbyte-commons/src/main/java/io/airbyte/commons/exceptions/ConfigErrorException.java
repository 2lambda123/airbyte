/*
 * Copyright (c) 2022 Airbyte, Inc., all rights reserved.
 */

package io.airbyte.commons.exceptions;

public class ConfigErrorException extends RuntimeException {

  private String displayMessage;

  public ConfigErrorException(final String displayMessage) {
    super(displayMessage);
  }

  public ConfigErrorException(final String displayMessage, final Throwable exception) {
    super(exception);
    this.displayMessage = displayMessage;
  }

  public String getDisplayMessage() {
    return displayMessage;
  }

}
