CREATE
    DATABASE MSSQL_FULL_NN;

USE MSSQL_FULL_NN;

CREATE
    TABLE
        dbo.TEST_DATASET(
            id INTEGER PRIMARY KEY,
            test_column_1 BIGINT,
            test_column_10 FLOAT,
            test_column_11 REAL,
            test_column_12 DATE,
            test_column_13 smalldatetime,
            test_column_14 datetime,
            test_column_15 datetime2,
            test_column_16 TIME,
            test_column_17 datetimeoffset,
            test_column_18 CHAR,
            test_column_19 VARCHAR(MAX) COLLATE Latin1_General_100_CI_AI_SC_UTF8,
            test_column_2 INT,
            test_column_20 text,
            test_column_21 nchar,
            test_column_22 nvarchar(MAX),
            test_column_23 ntext,
            test_column_24 BINARY,
            test_column_25 VARBINARY(3),
            test_column_26 geometry,
            test_column_27 uniqueidentifier,
            test_column_28 xml,
            test_column_29 geography,
            test_column_3 SMALLINT,
            test_column_30 hierarchyid,
            test_column_31 sql_variant,
            test_column_4 tinyint,
            test_column_5 bit,
            test_column_6 DECIMAL(
                5,
                2
            ),
            test_column_7 NUMERIC,
            test_column_8 money,
            test_column_9 smallmoney
        );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        1,
        - 9223372036854775808,
        '123',
        '123',
        '0001-01-01',
        '1900-01-01',
        '1753-01-01',
        '0001-01-01',
        '13:00:01',
        '0001-01-10 00:00:00 +01:00',
        'a',
        'a',
        - 2147483648,
        'a',
        'a',
        'a',
        'a',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '<user><user_id>1</user_id></user>',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        - 32768,
        '/1/1/',
        'a',
        0,
        0,
        999.33,
        '99999',
        '9990000.3647',
        '-214748.3648'
    );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        2,
        9223372036854775807,
        '1234567890.1234567',
        '1234567890.1234567',
        '9999-12-31',
        '2079-06-06',
        '9999-12-31',
        '9999-12-31',
        '13:00:04Z',
        '9999-01-10 00:00:00 +01:00',
        '*',
        'abc',
        2147483647,
        'abc',
        '*',
        'abc',
        'abc',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        32767,
        '/1/1/',
        'abc',
        255,
        1,
        999.33,
        '99999',
        '9990000.3647',
        214748.3647
    );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        3,
        0,
        '1234567890.1234567',
        '1234567890.1234567',
        '1999-01-08',
        '2079-06-06',
        '9999-12-31T13:00:04Z',
        '9999-12-31T13:00:04.123456Z',
        '13:00:04.123456Z',
        '9999-01-10 00:00:00 +01:00',
        '*',
        N'Миші йдуть на південь, не питай чому;',
        2147483647,
        'Some test text 123$%^&*()_',
        N'ї',
        N'Миші йдуть на південь, не питай чому;',
        N'Миші йдуть на південь, не питай чому;',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        32767,
        '/1/1/',
        N'Миші йдуть на південь, не питай чому;',
        255,
        'true',
        999.33,
        '99999',
        '9990000.3647',
        214748.3647
    );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        4,
        0,
        '1234567890.1234567',
        '1234567890.1234567',
        '1999-01-08',
        '2079-06-06',
        '9999-12-31T13:00:04.123Z',
        '9999-12-31T13:00:04.123456Z',
        '13:00:04.123456Z',
        '9999-01-10 00:00:00 +01:00',
        '*',
        N'櫻花分店',
        2147483647,
        '',
        N'ї',
        N'櫻花分店',
        N'櫻花分店',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        32767,
        '/1/1/',
        N'櫻花分店',
        255,
        'false',
        999.33,
        '99999',
        '9990000.3647',
        214748.3647
    );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        5,
        0,
        '1234567890.1234567',
        '1234567890.1234567',
        '1999-01-08',
        '2079-06-06',
        '9999-12-31T13:00:04.123Z',
        '9999-12-31T13:00:04.123456Z',
        '13:00:04.123456Z',
        '9999-01-10 00:00:00 +01:00',
        '*',
        '',
        2147483647,
        '',
        N'ї',
        '',
        '',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        32767,
        '/1/1/',
        '',
        255,
        'false',
        999.33,
        '99999',
        '9990000.3647',
        214748.3647
    );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        6,
        0,
        '1234567890.1234567',
        '1234567890.1234567',
        '1999-01-08',
        '2079-06-06',
        '9999-12-31T13:00:04.123Z',
        '9999-12-31T13:00:04.123456Z',
        '13:00:04.123456Z',
        '9999-01-10 00:00:00 +01:00',
        '*',
        N'\xF0\x9F\x9A\x80',
        2147483647,
        '',
        N'ї',
        N'\xF0\x9F\x9A\x80',
        N'\xF0\x9F\x9A\x80',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        32767,
        '/1/1/',
        N'\xF0\x9F\x9A\x80',
        255,
        'false',
        999.33,
        '99999',
        '9990000.3647',
        214748.3647
    );

INSERT
    INTO
        dbo.TEST_DATASET
    VALUES(
        7,
        0,
        '1234567890.1234567',
        '1234567890.1234567',
        '1999-01-08',
        '2079-06-06',
        '9999-12-31T13:00:04.123Z',
        '9999-12-31T13:00:04.123456Z',
        '13:00:04.123456Z',
        '9999-01-10 00:00:00 +01:00',
        '*',
        N'\xF0\x9F\x9A\x80',
        2147483647,
        '',
        N'ї',
        N'\xF0\x9F\x9A\x80',
        N'\xF0\x9F\x9A\x80',
        CAST(
            'A' AS BINARY(1)
        ),
        CAST(
            'ABC' AS VARBINARY
        ),
        geometry::STGeomFromText(
            'LINESTRING (100 100, 20 180, 180 180)',
            0
        ),
        '375CFC44-CAE3-4E43-8083-821D2DF0E626',
        '',
        geography::STGeomFromText(
            'LINESTRING(-122.360 47.656, -122.343 47.656 )',
            4326
        ),
        32767,
        '/1/1/',
        N'\xF0\x9F\x9A\x80',
        255,
        'false',
        999.33,
        '99999',
        '9990000.3647',
        214748.3647
    );
