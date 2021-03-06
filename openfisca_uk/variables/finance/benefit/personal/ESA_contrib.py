from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class ESA_contrib(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based)"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("ESA_contrib_reported", period)


class ESA_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = u"Employment and Support Allowance (contribution-based) (reported)"
    definition_period = WEEK
