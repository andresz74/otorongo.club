from django.core.management import BaseCommand

from votes.models import Elections, Person, Ingresos, CompiledPerson, BienMueble, BienInmueble, \
    CompiledOrg


class Command(BaseCommand):
    help = "Compile data for candidates. Computing all data in the fly is too costly"

    def handle(self, *args, **options):
        process()


def process():
    print("processing")
    # process_ingresos()
    # process_bienes()
    # process_sentencias()
    # process_partidos()
    process_partidos_por_region()


def process_partidos():
    # sentencias
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    for person in Person.objects.filter(elections=election):
        compiled_org, created = CompiledOrg.objects.get_or_create(
            name=person.strOrganizacionPolitica,
            idOrganizacionPolitica=person.idOrganizacionPolitica,
        )
        if created:
            print(f'created {compiled_org}')

        compiled_org.total_sentencia_penal += person.sentenciapenal_set.all().count()
        compiled_org.total_sentencia_obliga += person.sentenciaobliga_set.all().count()
        compiled_org.total_sentencias = compiled_org.total_sentencia_penal + \
                                        compiled_org.total_sentencia_obliga
        compiled_org.save()


def process_partidos_por_region():
    """Generate an aggregate of antecedentes per org politica per region"""
    # sentencias
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    for person in Person.objects.filter(elections=election):
        compiled_org, created = CompiledOrg.objects.get_or_create(
            name=person.strOrganizacionPolitica,
            postula_distrito=person.strPostulaDistrito,
            idOrganizacionPolitica=person.idOrganizacionPolitica,
        )
        if created:
            print(f'created {compiled_org}')

        compiled_org.total_sentencia_penal += person.sentenciapenal_set.all().count()
        compiled_org.total_sentencia_obliga += person.sentenciaobliga_set.all().count()
        compiled_org.total_sentencias = compiled_org.total_sentencia_penal + \
                                        compiled_org.total_sentencia_obliga
        compiled_org.save()


def process_sentencias():
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    for person in Person.objects.filter(elections=election):
        compiled_person, created = CompiledPerson.objects.get_or_create(
            person=person
        )
        if created:
            print(f'created {compiled_person}')

        compiled_person.sentencias_penales = person.sentenciapenal_set.all().count()
        compiled_person.sentencias_obliga = person.sentenciaobliga_set.all().count()
        compiled_person.sentencias_total = compiled_person.sentencias_penales + \
                                           compiled_person.sentencias_obliga
        compiled_person.save()


def process_bienes():
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    for person in Person.objects.filter(elections=election):
        compiled_person, created = CompiledPerson.objects.get_or_create(
            person=person
        )
        if created:
            print(f'created {compiled_person}')
        muebles = BienMueble.objects.filter(
            election=election,
            person=person,
        )
        if muebles:
            compiled_person.muebles = 0
            for mueble in muebles:
                compiled_person.muebles += mueble.decValor
        else:
            compiled_person.muebles = 0

        inmuebles = BienInmueble.objects.filter(
            election=election,
            person=person,
        )
        if inmuebles:
            compiled_person.inmuebles = 0
            for inmueble in inmuebles:
                compiled_person.inmuebles += inmueble.decAutovaluo
        else:
            compiled_person.inmuebles = 0

        compiled_person.total_muebles_inmuebles = compiled_person.inmuebles + compiled_person.muebles
        compiled_person.save()


def process_ingresos():
    election = Elections.objects.get(
        name='Elecciones Generales 2021'
    )
    for person in Person.objects.filter(elections=election):
        compiled_person, created = CompiledPerson.objects.get_or_create(
            person=person
        )
        if created:
            print(f'created {compiled_person}')
        ingresos = Ingresos.objects.filter(
            election=election,
            person=person,
        )
        if ingresos:
            ingreso = ingresos.first()
            compiled_person.ingreso = ingreso
            compiled_person.ingreso_total = \
                ingreso.decRemuBrutaPublico + \
                ingreso.decRemuBrutaPrivado + \
                ingreso.decRentaIndividualPublico + \
                ingreso.decRentaIndividualPrivado + \
                ingreso.decOtroIngresoPublico + \
                ingreso.decOtroIngresoPrivado
        else:
            compiled_person.ingreso_total = 0

        compiled_person.save()
