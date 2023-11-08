#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import os

import pytest
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from source_stripe.streams import (
    CreatedCursorIncrementalStripeStream,
    IncrementalStripeStream,
    ParentIncrementalStipeLazySubStream,
    StripeLazySubStream,
    StripeStream,
    UpdatedCursorIncrementalStripeLazySubStream,
    UpdatedCursorIncrementalStripeStream,
)

os.environ["REQUEST_CACHE_PATH"] = "REQUEST_CACHE_PATH"


@pytest.fixture(name="config")
def config_fixture():
    config = {"client_secret": "sk_test(live)_<secret>", "account_id": "<account_id>", "start_date": "2020-05-01T00:00:00Z"}
    return config


@pytest.fixture(name="stream_args")
def stream_args_fixture():
    authenticator = TokenAuthenticator("sk_test(live)_<secret>")
    args = {
        "authenticator": authenticator,
        "account_id": "<account_id>",
        "start_date": 1588315041,
        "slice_range": 365,
    }
    return args


@pytest.fixture(name="incremental_stream_args")
def incremental_args_fixture(stream_args):
    return {"lookback_window_days": 14, **stream_args}


@pytest.fixture(name="invoices")
def invoices_fixture(stream_args):
    def mocker(args=stream_args):
        return IncrementalStripeStream(
            name="invoices",
            path="invoices",
            use_cache=False,
            event_types=[
                "invoice.created",
                "invoice.finalization_failed",
                "invoice.finalized",
                "invoice.marked_uncollectible",
                "invoice.paid",
                "invoice.payment_action_required",
                "invoice.payment_failed",
                "invoice.payment_succeeded",
                "invoice.sent",
                "invoice.upcoming",
                "invoice.updated",
                "invoice.voided",
            ],
            **args,
        )

    return mocker


@pytest.fixture(name="invoice_line_items")
def invoice_line_items_fixture(invoices, stream_args):
    parent_stream = invoices()

    def mocker(args=stream_args, parent_stream=parent_stream):
        return StripeLazySubStream(
            name="invoice_line_items",
            path=lambda self, stream_slice, *args, **kwargs: f"invoices/{stream_slice['parent']['id']}/lines",
            parent=parent_stream,
            sub_items_attr="lines",
            slice_data_retriever=lambda record, stream_slice: {"invoice_id": stream_slice["parent"]["id"], **record},
            **args,
        )

    return mocker


@pytest.fixture()
def accounts(stream_args):
    def mocker(args=stream_args):
        return StripeStream(name="accounts", path="accounts", **args)

    return mocker


@pytest.fixture()
def balance_transactions(incremental_stream_args):
    def mocker(args=incremental_stream_args):
        return CreatedCursorIncrementalStripeStream(name="balance_transactions", path="balance_transactions", **args)

    return mocker


@pytest.fixture()
def credit_notes(stream_args):
    def mocker(args=stream_args):
        return UpdatedCursorIncrementalStripeStream(
            name="credit_notes",
            path="credit_notes",
            event_types=["credit_note.created", "credit_note.updated", "credit_note.voided"],
            **args,
        )

    return mocker


@pytest.fixture()
def customers(stream_args):
    def mocker(args=stream_args):
        return IncrementalStripeStream(
            name="customers",
            path="customers",
            use_cache=False,
            expand_items=["data.sources"],
            event_types=["customer.created", "customer.updated"],
            **args,
        )

    return mocker


@pytest.fixture()
def bank_accounts(customers, stream_args):
    parent_stream = customers()

    def mocker(args=stream_args, parent_stream=parent_stream):
        return UpdatedCursorIncrementalStripeLazySubStream(
            name="bank_accounts",
            path=lambda self, stream_slice, *args, **kwargs: f"customers/{stream_slice['parent']['id']}/sources",
            parent=parent_stream,
            event_types=["customer.source.created", "customer.source.expiring", "customer.source.updated", "customer.source.deleted"],
            legacy_cursor_field=None,
            sub_items_attr="sources",
            extra_request_params={"object": "bank_account"},
            response_filter=lambda record: record["object"] == "bank_account",
            **args,
        )

    return mocker


@pytest.fixture()
def external_bank_accounts(stream_args):
    def mocker(args=stream_args):
        return UpdatedCursorIncrementalStripeStream(
            name="external_account_bank_accounts",
            path=lambda self, *args, **kwargs: f"accounts/{self.account_id}/external_accounts",
            event_types=["account.external_account.created", "account.external_account.updated", "account.external_account.deleted"],
            legacy_cursor_field=None,
            extra_request_params={"object": "bank_account"},
            response_filter=lambda record: record["object"] == "bank_account",
            **args,
        )

    return mocker


@pytest.fixture(name="subscriptions")
def subscription_fixture(stream_args):
    def mocker(args=stream_args):
        return IncrementalStripeStream(
            name="subscriptions",
            path="subscriptions",
            use_cache=False,
            extra_request_params={"status": "all"},
            event_types=[
                "customer.subscription.created",
                "customer.subscription.paused",
                "customer.subscription.pending_update_applied",
                "customer.subscription.pending_update_expired",
                "customer.subscription.resumed",
                "customer.subscription.trial_will_end",
                "customer.subscription.updated",
                "customer.subscription.deleted",
            ],
            **args,
        )

    return mocker


@pytest.fixture(name="subscription_items")
def subscription_items_fixture(subscriptions, stream_args):
    parent_stream = subscriptions()

    def mocker(args=stream_args, parent_stream=parent_stream):
        return StripeLazySubStream(
            name="subscription_items",
            path="subscription_items",
            extra_request_params=lambda self, stream_slice, *args, **kwargs: {"subscription": stream_slice["parent"]["id"]},
            parent=parent_stream,
            use_cache=False,
            sub_items_attr="items",
            **args,
        )

    return mocker


@pytest.fixture(name="application_fees")
def application_fees_fixture(stream_args):
    def mocker(args=stream_args):
        return IncrementalStripeStream(
            name="application_fees",
            path="application_fees",
            use_cache=False,
            event_types=["application_fee.created", "application_fee.refunded"],
            **args,
        )

    return mocker


@pytest.fixture(name="application_fees_refunds")
def application_fees_refunds_fixture(application_fees, stream_args):
    parent_stream = application_fees()

    def mocker(args=stream_args, parent_stream=parent_stream):
        return UpdatedCursorIncrementalStripeLazySubStream(
            name="application_fees_refunds",
            path=lambda self, stream_slice, *args, **kwargs: f"application_fees/{stream_slice['parent']['id']}/refunds",
            parent=parent_stream,
            event_types=["application_fee.refund.updated"],
            sub_items_attr="refunds",
            **args,
        )

    return mocker


@pytest.fixture(name="checkout_sessions")
def checkout_sessions_fixture(stream_args):
    def mocker(args=stream_args):
        return UpdatedCursorIncrementalStripeStream(
            name="checkout_sessions",
            path="checkout/sessions",
            use_cache=False,
            legacy_cursor_field="created",
            event_types=[
                "checkout.session.async_payment_failed",
                "checkout.session.async_payment_succeeded",
                "checkout.session.completed",
                "checkout.session.expired",
            ],
            **args,
        )

    return mocker


@pytest.fixture(name="checkout_sessions_line_items")
def checkout_sessions_line_items_fixture(checkout_sessions, stream_args):
    parent_stream = checkout_sessions()

    def mocker(args=stream_args, parent_stream=parent_stream):
        return ParentIncrementalStipeLazySubStream(
            name="checkout_sessions_line_items",
            path=lambda self, stream_slice, *args, **kwargs: f"checkout/sessions/{stream_slice['parent']['id']}/line_items",
            parent=parent_stream,
            expand_items=["data.discounts", "data.taxes"],
            cursor_field="checkout_session_updated",
            slice_data_retriever=lambda record, stream_slice: {
                "checkout_session_id": stream_slice["parent"]["id"],
                "checkout_session_expires_at": stream_slice["parent"]["expires_at"],
                "checkout_session_created": stream_slice["parent"]["created"],
                "checkout_session_updated": stream_slice["parent"]["updated"],
                **record,
            },
            **args,
        )

    return mocker
