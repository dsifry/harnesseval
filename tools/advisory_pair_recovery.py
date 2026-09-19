"""Explicit request-side schema recovery; never silently rewrite pair evidence."""
import copy


SCHEMA_CLARIFICATION = '''

OUTPUT SCHEMA CLARIFICATION FOR THIS RETRY:
All mechanism, trigger, and consequence fields must be non-empty strings. If a
claim does not state one of these details, write the literal "not stated" for
that field. Do not infer or invent missing claim details. Do not leave fields
empty or omit any numbered pair. All equivalence rules above remain unchanged;
this clarification does not establish equivalence for missing information.
'''


def schema_recovery_request(original):
    request = copy.deepcopy(original)
    request['prompt'] += SCHEMA_CLARIFICATION
    return request
