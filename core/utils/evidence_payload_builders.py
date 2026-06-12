from copy import deepcopy


POS_ATTRIBUTE_DETAILS = {
    "70060213": {"type": "String", "name": "DOCUMENT_TYPE"},
    "349876894": {"type": "String", "name": "OFFER"},
    "425747132": {"type": "String", "name": "SENDING_FORM"},
    "447500851": {"type": "String", "name": "ACCOUNT"},
    "908881601": {"type": "Long", "name": "ACCOUNT_STATE"},
    "1576075623": {"type": "String", "name": "PAYMENT_METHOD"},
    "1597489127": {"type": "String", "name": "External Id"},
    "1666101552": {"type": "String", "name": "DOCUMENT_ID"},
    "1667261676": {"type": "Long", "name": "MSISDN"},
    "1794057286": {"type": "String", "name": "BILLING_ACCOUNT_STATE"},
    "1840045565": {"type": "Long", "name": "BILLING_CYCLE_CUT_OFF_DAY"},
    "1997035279": {"type": "Long", "name": "BILLING_CYCLE"},
    "2020041941": {"type": "Long", "name": "CLIENT_TYPE"},
    "2118173840": {"type": "String", "name": "BILLING_ACCOUNT"},
}


PRE_ATTRIBUTE_DETAILS = {
    "29905344": {"type": "Long", "name": "COMPANY_OPERATOR"},
    "427862433": {"type": "String", "name": "AREA_CODE"},
    "447500851": {"type": "String", "name": "ACCOUNT"},
    "569463775": {"type": "Date", "name": "PROFILE_DATE"},
    "741842957": {"type": "Long", "name": "MULTI_OPERATION"},
    "908881601": {"type": "Long", "name": "ACCOUNT_STATE"},
    "1068616960": {"type": "Date", "name": "ACCOUNT_PROVISION_DATE"},
    "1095579373": {"type": "String", "name": "GEOGRAPHICAL_STATE"},
    "1190622368": {"type": "Long", "name": "PROFILE"},
    "1358620105": {"type": "Long", "name": "PRODUCT_TYPE"},
    "1581479658": {"type": "String", "name": "GRUPO CONTROLE UNIVERSAL"},
    "1597489127": {"type": "String", "name": "EXTERNAL_ID"},
    "1650737577": {"type": "Long", "name": "PORTABILITY_SITUATION"},
    "1667261676": {"type": "Long", "name": "MSISDN"},
    "1760625139": {"type": "Long", "name": "REASON_CODE"},
    "1944018544": {"type": "String", "name": "CLIENT_OWNER"},
    "1957846968": {"type": "String", "name": "NOTIFY_PERMISSIONS"},
    "1966426172": {"type": "Date", "name": "ACCOUNT_STATE_DATE"},
    "2020041941": {"type": "Long", "name": "CLIENT_TYPE"},
    "2047205742": {"type": "Date", "name": "ACCOUNT_ACTIVATION_DATE"},
}


def build_postpaid_payload(msisdn, offer, event_time):
    account = msisdn[3:]
    external_id = f"NEXT_{account}"

    payload = {
        "operation": "processEvent",
        "extEventId": 986557550,
        "eventTime": event_time,
        "attributes": {
            "70060213": "1",
            "349876894": offer,
            "425747132": "EMAIL",
            "447500851": account,
            "908881601": "1",
            "1576075623": "DD",
            "1597489127": external_id,
            "1666101552": "1",
            "1667261676": msisdn,
            "1794057286": "1791234567",
            "1840045565": "5",
            "1997035279": "5",
            "2020041941": "2",
            "2118173840": "365123987",
        },
    }

    return attach_attribute_details(payload, POS_ATTRIBUTE_DETAILS), external_id


def build_prepaid_payload(msisdn, event_time, attribute_time, profile="559", account_state="2"):
    account = msisdn[3:]
    external_id = f"NGIN_{account}"

    payload = {
        "operation": "processEvent",
        "extEventId": 866231225,
        "eventTime": event_time,
        "attributes": {
            "29905344": "8",
            "427862433": "11",
            "447500851": account,
            "569463775": attribute_time,
            "741842957": "1",
            "908881601": account_state,
            "1068616960": attribute_time,
            "1095579373": "SP",
            "1190622368": profile,
            "1358620105": "3",
            "1581479658": "S",
            "1597489127": external_id,
            "1650737577": "1",
            "1667261676": msisdn,
            "1760625139": "1",
            "1944018544": "NGIN",
            "1957846968": "0000000D",
            "1966426172": attribute_time,
            "2020041941": "1",
            "2047205742": attribute_time,
        },
    }

    return attach_attribute_details(payload, PRE_ATTRIBUTE_DETAILS), external_id


def attach_attribute_details(payload, metadata):
    attributes = payload.get("attributes") or {}
    missing_metadata = sorted(set(attributes) - set(metadata))
    if missing_metadata:
        raise ValueError(f"missing metadata for attributes: {', '.join(missing_metadata)}")

    payload_with_details = deepcopy(payload)
    payload_with_details["attributeDetails"] = {
        key: deepcopy(metadata[key]) for key in attributes
    }
    return payload_with_details
