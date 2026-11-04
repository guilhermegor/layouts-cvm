"""layouts-cvm — CVM submission (envio) layouts.

Every "envio" solution lives here: a writer takes plain data (a mapping) or an
already-built document model, validates it, and produces a CVM-compliant file ready
to submit. The document models are private (``_internal.config.schemas``) and are not
exported; pass a mapping to the writer:

    from layouts_cvm import PerfilMensal

    PerfilMensal().export(dict_document, "perfil_mensal.xml")
"""

from importlib.metadata import PackageNotFoundError, version

from layouts_cvm.cadastro_ativos import CadastroAtivos
from layouts_cvm.cda import Cda
from layouts_cvm.cda_v2 import CdaV2
from layouts_cvm.cda_v3 import CdaV3
from layouts_cvm.extrato import Extrato
from layouts_cvm.extrato_v2 import ExtratoV2
from layouts_cvm.inf_fundo_157 import InfFundo157
from layouts_cvm.inf_mensal_fidc import InfMensalFidc
from layouts_cvm.inf_mensal_fidc_489 import InfMensalFidc489
from layouts_cvm.informe_diario import InformeDiario
from layouts_cvm.informe_diario_v2 import InformeDiarioV2
from layouts_cvm.informe_diario_v3 import InformeDiarioV3
from layouts_cvm.informe_portabilidade import InformePortabilidade
from layouts_cvm.informe_quadrimestral import InformeQuadrimestral
from layouts_cvm.informe_trimestral_v1 import InformeTrimestralV1
from layouts_cvm.inr_mensal import InrMensal
from layouts_cvm.lamina import Lamina
from layouts_cvm.lamina_v1 import LaminaV1
from layouts_cvm.lamina_v2 import LaminaV2
from layouts_cvm.main import main
from layouts_cvm.perfil_mensal import PerfilMensal
from layouts_cvm.perfil_mensal_original import PerfilMensalOriginal
from layouts_cvm.perfil_mensal_v3 import PerfilMensalV3


try:
    __version__ = version("layouts-cvm")
except PackageNotFoundError:  # pragma: no cover - source tree without an installed dist
    __version__ = "0.0.0"


__all__ = [
    "__version__",
    "main",
    "CadastroAtivos",
    "Cda",
    "CdaV3",
    "CdaV2",
    "Extrato",
    "ExtratoV2",
    "InfFundo157",
    "InfMensalFidc",
    "InfMensalFidc489",
    "InformeDiario",
    "InformeDiarioV2",
    "InformeDiarioV3",
    "InformePortabilidade",
    "InformeQuadrimestral",
    "InformeTrimestralV1",
    "InrMensal",
    "Lamina",
    "LaminaV1",
    "LaminaV2",
    "PerfilMensal",
    "PerfilMensalOriginal",
    "PerfilMensalV3",
]
