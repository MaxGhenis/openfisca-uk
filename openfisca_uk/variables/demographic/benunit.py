from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class benunit_weight(Variable):
    value_type = float
    entity = Household
    label = u'Weight factor for the benefit unit'
    definition_period = YEAR