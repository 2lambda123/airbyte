#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from airbyte_cdk.sources.config import BaseConfig
from facebook_business.adobjects.adsinsights import AdsInsights
from pydantic import BaseModel, Field, PositiveInt

logger = logging.getLogger("airbyte")


ValidFields = Enum("Valid AdsInsights Fields", AdsInsights.Field.__dict__)
ValidFields.__doc__ = "An enumeration of valid fields for custom insights, imported from the Facebook Business SDK"
ValidBreakdowns = Enum("Valid AdsInsights Breakdowns", AdsInsights.Breakdowns.__dict__)
ValidBreakdowns.__doc__ = "An enumeration of valid breakdowns for custom insights, imported from the Facebook Business SDK"
ValidActionBreakdowns = Enum("Valid AdsInsights Action Breakdowns", AdsInsights.ActionBreakdowns.__dict__)
ValidActionBreakdowns.__doc__ = "An enumeration of valid action breakdowns for custom insights, imported from the Facebook Business SDK"
DATE_TIME_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
EMPTY_PATTERN = "^$"


class InsightConfig(BaseModel):
    """Config for custom insights"""

    class Config:
        use_enum_values = True

    name: str = Field(
        title="Name",
        description="The name of the custom insight. This will be used as the Airbyte stream name.",
        order=0,
    )

    level: str = Field(
        title="Level",
        description="The granularity level for data retrieval of the custom insight from the API.",
        default="ad",
        enum=["ad", "adset", "campaign", "account"],
        order=1,
    )

    fields: Optional[List[ValidFields]] = Field(
        title="Fields",
        description="Use the dropdown menu to add the desired fields for your custom insight.",
        default=[],
        order=2,
    )

    breakdowns: Optional[List[ValidBreakdowns]] = Field(
        title="Breakdowns",
        description="Use the dropdown menu to add the desired breakdowns for your custom insight.",
        default=[],
        order=3,
    )

    action_breakdowns: Optional[List[ValidActionBreakdowns]] = Field(
        title="Action Breakdowns",
        description="Use the dropdown menu to add the desired action breakdowns for your custom insight.",
        default=[],
        order=4,
    )

    action_report_time: str = Field(
        title="Action Report Time",
        description=(
            "This value determines the timing used to report action statistics. For example, if a user sees an ad on Jan 1st "
            "but converts on Jan 2nd, this value will determine how the action is reported. "
            "When set to impression, you see a conversion on Jan 1st. "
            "When set to conversion, you see a conversion on Jan 2nd. "
            "When set to mixed, view-through actions are reported at the time of the impression and click-through actions are reported at the time of conversion."
        ),
        default="mixed",
        enum=["conversion", "impression", "mixed"],
        order=5,
    )

    time_increment: Optional[PositiveInt] = Field(
        title="Time Increment",
        description=(
            "The time window in days by which to aggregate statistics. The sync will be chunked into N day intervals, where N is the number of days you specified. "
            "For example, if you set this value to 7, then all statistics will be reported as 7-day aggregates by starting from the start_date. If the start and end dates are October 1st and October 30th, then the connector will output 5 records: 01 - 06, 07 - 13, 14 - 20, 21 - 27, and 28 - 30 (3 days only)."
        ),
        exclusiveMaximum=90,
        default=1,
        order=6,
    )

    start_date: Optional[datetime] = Field(
        title="Start Date",
        description="The date from which you'd like to replicate data for this stream, in the format YYYY-MM-DDT00:00:00Z. Leaving this field blank will replicate all data.",
        pattern=DATE_TIME_PATTERN,
        examples=["2017-01-25T00:00:00Z"],
        order=7,
    )

    end_date: Optional[datetime] = Field(
        title="End Date",
        description=(
            "The date until which you'd like to replicate data for this stream, in the format YYYY-MM-DDT00:00:00Z. "
            "All data generated between the start date and this end date will be replicated. "
            "Not setting this option will result in always syncing the latest data."
        ),
        pattern=DATE_TIME_PATTERN,
        examples=["2017-01-26T00:00:00Z"],
        order=8,
    )
    insights_lookback_window: Optional[PositiveInt] = Field(
        title="Custom Insights Lookback Window",
        description=(
            "The number of days to revisit data during syncing to capture updated conversion data from the API. "
            "Facebook allows for attribution windows of up to 28 days, during which time a conversion can be attributed to an ad."
            "If you have set a custom attribution window in your Facebook account, please set the same value here. "
            "Refer to the <a href='https://docs.airbyte.com/integrations/sources/facebook-marketing'>docs</a> for more information on this value."
        ),
        maximum=28,
        mininum=1,
        default=28,
        order=9,
    )


class ConnectorConfig(BaseConfig):
    """Connector config"""

    class Config:
        title = "Source Facebook Marketing"

    account_id: str = Field(
        title="Ad Account ID",
        order=0,
        description=(
            "The Facebook Ad account ID to use when pulling data from the Facebook Marketing API. "
            "The Ad account ID number is in the account dropdown menu or in your browser's address "
            'bar of your <a href="https://adsmanager.facebook.com/adsmanager/">Meta Ads Manager</a>. '
            'See the <a href="https://www.facebook.com/business/help/1492627900875762">docs</a> for more information.'
        ),
        pattern="^[0-9]+$",
        pattern_descriptor="1234567890",
        examples=["111111111111111"],
    )

    access_token: str = Field(
        title="Access Token",
        order=1,
        description=(
            "The value of the generated access token. "
            'From your App’s Dashboard, click on "Marketing API" then "Tools". '
            'Select permissions <b>ads_management, ads_read, read_insights, business_management</b>. Then click on "Get token". '
            'See the <a href="https://docs.airbyte.com/integrations/sources/facebook-marketing">docs</a> for more information.'
        ),
        airbyte_secret=True,
    )

    start_date: Optional[datetime] = Field(
        title="Start Date",
        order=2,
        description=(
            "The date from which you'd like to replicate data for all incremental streams, "
            "in the format YYYY-MM-DDT00:00:00Z. If not set then all data will be replicated for usual streams and only last 2 years for insight streams."
        ),
        pattern=DATE_TIME_PATTERN,
        examples=["2017-01-25T00:00:00Z"],
    )

    end_date: Optional[datetime] = Field(
        title="End Date",
        order=3,
        description=(
            "The date until which you'd like to replicate data for all incremental streams, in the format YYYY-MM-DDT00:00:00Z. "
            "All data generated between the start date and this end date will be replicated. "
            "Not setting this option will result in always syncing the latest data."
        ),
        pattern=EMPTY_PATTERN + "|" + DATE_TIME_PATTERN,
        examples=["2017-01-26T00:00:00Z"],
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )

    include_deleted: bool = Field(
        title="Include Deleted Campaigns, Ads, and AdSets",
        order=4,
        default=False,
        description="Set to active if you want to include data from deleted Campaigns, Ads, and AdSets.",
    )

    fetch_thumbnail_images: bool = Field(
        title="Fetch Thumbnail Images from Ad Creative",
        order=5,
        default=False,
        description="Set to active if you want to fetch the thumbnail_url and store the result in thumbnail_data_url for each Ad Creative.",
    )

    custom_insights: Optional[List[InsightConfig]] = Field(
        title="Custom Insights",
        order=6,
        description=(
            "A list which contains custom ad statistics entries. Each entry must have a name and can contains fields, "
            "breakdowns and/or action_breakdowns. Click on 'Add' to fill this field. "
            "For more information on configuring custom insights, refer to the <a href='https://docs.airbyte.com/integrations/sources/facebook-marketing'>docs</a>."
        ),
    )

    page_size: Optional[PositiveInt] = Field(
        title="Page Size of Requests",
        order=7,
        default=100,
        description=(
            "Page size used when sending requests to Facebook API to specify number of records per page when response has pagination. "
            "Most users do not need to set this field unless they need to tune the connector to address specific issues or use cases."
        ),
    )

    insights_lookback_window: Optional[PositiveInt] = Field(
        title="Insights Lookback Window",
        order=8,
        description=(
            "The number of days to revisit data during syncing to capture updated conversion data from the API. "
            "Facebook allows for attribution windows of up to 28 days, during which time a conversion can be attributed to an ad."
            "If you have set a custom attribution window in your Facebook account, please set the same value here. "
            "Refer to the <a href='https://docs.airbyte.com/integrations/sources/facebook-marketing'>docs</a> for more information on this value."
        ),
        maximum=28,
        mininum=1,
        default=28,
    )


    action_breakdowns_allow_empty: bool = Field(
        description="Allows action_breakdowns to be an empty list",
        default=True,
        airbyte_hidden=True,
    )

    client_id: Optional[str] = Field(
        description="The Client Id for your OAuth app",
        airbyte_secret=True,
        airbyte_hidden=True,
    )

    client_secret: Optional[str] = Field(
        description="The Client Secret for your OAuth app",
        airbyte_secret=True,
        airbyte_hidden=True,
    )
