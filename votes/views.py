from django.contrib.postgres.search import SearchQuery
from django.core.paginator import InvalidPage
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.core import serializers
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.csrf import csrf_exempt

from votes.models import Person, Elections, Ingresos, BienMueble, \
                            BienInmueble, CompiledPerson, CompiledOrg, \
                            EduBasica, EduNoUniversitaria, EduTecnica, \
                            InfoAdicional, CargoEleccion, ExperienciaLaboral, \
                            CargoPartidario, RenunciaOrganizacionPolitica
from votes.utils import Paginator

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


def index(request):
    return render(
        request,
        'votes/index.html'
    )


@csrf_exempt
def search(request):
    context, election = make_context()
    query = request.GET.get('q') or ''
    query = query.strip()

    all_items = Person.objects.filter(
        full_search=SearchQuery(query),
        elections=election,
    ).order_by('last_names')
    context['all_items'] = all_items
    context['all_items_count'] = all_items.count()
    context['query'] = query

    return render(
        request,
        'votes/search.html',
        context,
    )


def ingresos_2021(request):
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    context = {'election': election}

    persons = CompiledPerson.objects.filter(
        person__elections=election,
    ).order_by('-ingreso_total')

    paginator, page = do_pagination(request, persons)
    context['candidates'] = paginator
    context['page'] = page

    return render(
        request,
        'votes/ingresos.html',
        context,
    )

def ingresos_2021_json(request):
    election = make_context()[1]
    persons = CompiledPerson.objects.filter(
        person__elections=election,
    ).order_by('-ingreso_total')

    data = []
    for candidate in persons:
        has_ingreso = candidate.ingreso != None

        obj = {}
        obj['nombre'] = f"{candidate.person.last_names} "\
            + candidate.person.first_names
        obj['dni'] = candidate.person.dni_number
        obj['partido'] = candidate.person.strOrganizacionPolitica
        obj['total_ingreso'] = candidate.ingreso_total
        obj['ingreso_publico'] = candidate.ingreso.decRemuBrutaPublico if has_ingreso else 0
        obj['ingreso_privado'] = candidate.ingreso.decRemuBrutaPrivado if has_ingreso else 0
        obj['renta_publico'] = candidate.ingreso.decRentaIndividualPublico if has_ingreso else 0
        obj['renta_privado'] = candidate.ingreso.decRentaIndividualPrivado if has_ingreso else 0
        obj['otro_ingreso_publico'] = candidate.ingreso.decOtroIngresoPublico if has_ingreso else 0
        obj['otro_ingreso_privado'] = candidate.ingreso.decOtroIngresoPrivado if has_ingreso else 0
        data.append(obj)

    return JsonResponse(data, safe=False)

def sentencias_2021(request, org_id = None):
    region = request.GET.get('region')
    context, election = make_context()
    persons = CompiledPerson.objects.filter(
        person__elections=election,
    ).order_by('-sentencias_total')

    if region and region == 'TODAS':
        pass
    elif region:
        persons = persons.filter(person__strPostulaDistrito=region)

    if org_id:
        persons = persons.filter(person__idOrganizacionPolitica=org_id)
        org = CompiledOrg.objects.filter(idOrganizacionPolitica=org_id).first()
        context['org_name'] = org.name

    paginator, page = do_pagination(request, persons)
    context['candidates'] = paginator
    context['page'] = page
    context['org_id'] = org_id

    return render(
        request,
        'votes/sentencias.html',
        context,
    )

def sentencias_2021_json(request):
    election = make_context()[1]
    persons = CompiledPerson.objects.filter(
        person__elections=election,
    ).order_by('-sentencias_total')

    data = []
    for candidate in persons:
        obj = {}
        obj['nombre'] = f"{candidate.person.last_names} "\
            + f"{candidate.person.first_names}"
        obj['dni'] = candidate.person.dni_number
        obj['organizacion_politica'] = candidate.person.strOrganizacionPolitica
        obj['total_antecedents'] = candidate.sentencias_total
        obj['antecedentes_penales'] = candidate.sentencias_penales
        obj['antecedentes_obligaciones'] = candidate.sentencias_obliga
        data.append(obj)

    return JsonResponse(data, safe=False)


def bienes_2021(request):
    context, election = make_context()

    persons = CompiledPerson.objects.filter(
        person__elections=election
    ).order_by('-total_muebles_inmuebles')

    paginator, page = do_pagination(request, persons)
    context['candidates'] = paginator
    context['page'] = page

    return render(
        request,
        'votes/bienes.html',
        context,
    )

def bienes_2021_json(request):
    election = make_context()[1]
    persons = CompiledPerson.objects.filter(
        person__elections=election
    ).order_by('-total_muebles_inmuebles')

    data = []
    for candidate in persons:
        obj = {}
        obj['nombre'] = f"{candidate.person.last_names} "\
            + f"{candidate.person.first_names}"
        obj['dni'] = candidate.person.dni_number
        obj['partido'] = candidate.person.strOrganizacionPolitica
        obj['total_muebles_inmuebles'] = candidate.total_muebles_inmuebles
        obj['muebles'] = candidate.muebles
        obj['inmuebles'] = candidate.inmuebles
        data.append(obj)

    return JsonResponse(data, safe=False)

def make_context():
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    context = {'election': election}
    return context, election


def partidos_sentencias_2021(request):
    region = request.GET.get('region')
    context, election = make_context()
    orgs = CompiledOrg.objects.all().order_by('-total_sentencias')

    if region and region == 'TODAS':
        orgs = orgs.filter(postula_distrito__isnull=True)
    elif region:
        orgs = orgs.filter(postula_distrito=region)

    context['orgs'] = orgs
    context['region'] = region
    return render(
        request,
        'votes/partido_sentencias.html',
        context,
    )


def partido_2021(request, org_id):
    context, election = make_context()
    context['candidates'] = CompiledPerson.objects.filter(
        person__idOrganizacionPolitica=org_id,
        person__elections=election,
    )
    return render(
        request,
        'votes/partido.html',
        context,
    )


def candidato_2021(request, dni):
    context, election = make_context()
    person = Person.objects.filter(
        dni_number=dni,
        elections=election,
    )
    if not person:
        raise Http404(f'no tenemos candidato con ese dni {dni}')

    person = person.first()
    context['candidate'] = person
    params_filter = {
        'person': person,
        'election': election,
    }
    context['muebles'] = BienMueble.objects.filter(**params_filter)
    context['inmuebles'] = BienInmueble.objects.filter(**params_filter)
    context['ingresos'] = Ingresos.objects.filter(**params_filter).first()
    if context['ingresos']:
        context['ingresos_total'] = context['ingresos'].decRemuBrutaPublico + \
                                    context['ingresos'].decRemuBrutaPrivado + \
                                    context['ingresos'].decRentaIndividualPublico + \
                                    context['ingresos'].decRentaIndividualPrivado + \
                                    context['ingresos'].decOtroIngresoPublico + \
                                    context['ingresos'].decOtroIngresoPrivado
    context['sentencias_penal'] = person.sentenciapenal_set.all()
    context['sentencias_obliga'] = person.sentenciaobliga_set.all()
    context['compiled_person'] = CompiledPerson.objects.get(
        person=person
    )
    
    context['edu_basica'] = EduBasica.objects.filter(**params_filter).first()
    context['edu_tecnica'] = EduTecnica.objects.filter(**params_filter).first()
    context['edu_nouniversitaria'] = EduNoUniversitaria.objects.filter(**params_filter).first()
    context['info_adicional'] = InfoAdicional.objects.filter(**params_filter).first()
    context['cargo_eleccion'] = CargoEleccion.objects.filter(**params_filter).all()
    context['experiencia_laboral'] = ExperienciaLaboral.objects.filter(**params_filter).all()
    context['cargo_partidario'] = CargoPartidario.objects.filter(**params_filter).all()
    context['renuncia_organizacion_politica'] = RenunciaOrganizacionPolitica.objects.filter(**params_filter).all()

    return render(
        request,
        'votes/candidate.html',
        context,
    )


def do_pagination(request, all_items):
    """
    :param request: contains the current page requested by user
    :param all_items:
    :return: dict containing paginated items and pagination bar
    """
    results_per_page = 50
    results = all_items

    try:
        page_no = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        raise Http404("Not a valid number for page.")

    if page_no < 1:
        raise Http404("Pages should be 1 or greater.")

    paginator = Paginator(results, results_per_page)

    try:
        page = paginator.page(page_no)
    except InvalidPage:
        raise Http404("No such page!")

    return paginator, page
