/*
 * Copyright (c) 2022 Airbyte, Inc., all rights reserved.
 */

package io.airbyte.api.server.repositories.clients;

import static io.micronaut.http.HttpHeaders.ACCEPT;
import static io.micronaut.http.HttpHeaders.USER_AGENT;

import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Header;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;

@Client(ClientConfigs.API_URL)
@Header(name = USER_AGENT,
        value = "Micronaut HTTP Client")
@Header(name = ACCEPT,
        value = "application/json")
public interface ConfigApiClient {

  @Post(value = "/api/v1/connections/sync",
        processes = MediaType.APPLICATION_JSON)
  HttpResponse<String> sync(@Body SyncDto connectionId);

  @Post(value = "/api/v1/connections/reset",
        consumes = MediaType.APPLICATION_JSON,
        produces = MediaType.APPLICATION_JSON)
  HttpResponse<String> reset(@Body SyncDto connectionId);

  @Post(value = "/api/v1/workspaces/list")
  HttpResponse<String> workspaceList();

  @Get("/health")
  HttpResponse<String> healthCheck();

}
