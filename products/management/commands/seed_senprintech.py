from django.core.management.base import BaseCommand

from products.models import DEFAULT_PRODUCT_PRICES, Category, Product, ProductOption, ProductOptionChoice


class Command(BaseCommand):
    help = "Create a clean SenPrinTech ecommerce catalogue."

    def handle(self, *args, **options):
        categories = [
            ("Cartes de visite", "cartes-de-visite"),
            ("Flyers", "flyers"),
            ("Brochures", "brochures"),
            ("Stickers", "stickers"),
            ("Mugs", "mugs"),
            ("T-shirts", "t-shirts"),
            ("Roll-up", "roll-up"),
            ("Papeterie", "papeterie"),
        ]

        for name, slug in categories:
            Category.objects.update_or_create(slug=slug, defaults={"name": name})

        products = [
            {
                "category": "cartes-de-visite",
                "name": "Cartes de visite",
                "slug": "cartes-de-visite",
                "description": "Cartes professionnelles sur papier premium.",
                "price": DEFAULT_PRODUCT_PRICES["cartes-de-visite"],
                "image": "products/business-cards-hd.png",
            },
            {
                "category": "flyers",
                "name": "Flyers",
                "slug": "flyers",
                "description": "Flyers A5, A4 ou A3 pour vos campagnes.",
                "price": DEFAULT_PRODUCT_PRICES["flyers"],
                "image": "products/flyers-hd.png",
            },
            {
                "category": "roll-up",
                "name": "Roll-up",
                "slug": "roll-up",
                "description": "Supports salons, boutiques et evenements.",
                "price": DEFAULT_PRODUCT_PRICES["roll-up"],
                "image": "products/rollup.jpg",
            },
            {
                "category": "t-shirts",
                "name": "T-shirts personnalises",
                "slug": "t-shirts-personnalises",
                "description": "Impression textile pour equipes et marques.",
                "price": DEFAULT_PRODUCT_PRICES["t-shirts-personnalises"],
                "image": "products/tshirts-hd.png",
            },
            {
                "category": "mugs",
                "name": "Mugs personnalises",
                "slug": "mugs-personnalises",
                "description": "Mugs imprimes pour cadeaux et bureaux.",
                "price": DEFAULT_PRODUCT_PRICES["mugs-personnalises"],
                "image": "products/mugs-hd.png",
            },
            {
                "category": "stickers",
                "name": "Stickers",
                "slug": "stickers",
                "description": "Stickers branding, packaging et evenements.",
                "price": DEFAULT_PRODUCT_PRICES["stickers"],
                "image": "products/stickers-hd.png",
            },
            {
                "category": "brochures",
                "name": "Brochures & Depliants",
                "slug": "brochures-depliants",
                "description": "Supports plies pour presenter vos offres.",
                "price": DEFAULT_PRODUCT_PRICES["brochures-depliants"],
                "image": "products/brochures-hd.png",
            },
            {
                "category": "papeterie",
                "name": "Enveloppes & Papier entete",
                "slug": "enveloppes-papier-entete",
                "description": "Papeterie professionnelle pour votre marque.",
                "price": DEFAULT_PRODUCT_PRICES["enveloppes-papier-entete"],
                "image": "products/enveloppe.jpg",
            },
        ]

        canonical_slugs = [item["slug"] for item in products]
        Product.objects.exclude(slug__in=canonical_slugs).update(available=False)

        created_count = 0
        updated_count = 0
        for item in products:
            category = Category.objects.get(slug=item["category"])
            product, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "category": category,
                    "name": item["name"],
                    "description": item["description"],
                    "price": item["price"],
                    "image": item["image"],
                    "available": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        option_specs = {
            "cartes-de-visite": [
                ("Quantite", "quantite", "select", True, [("100", "100", 0), ("250", "250", 6000), ("500", "500", 13000), ("1000", "1000", 24000)]),
                ("Papier", "papier", "select", True, [("Standard", "standard", 0), ("Premium", "premium", 2500), ("Luxe", "luxe", 6000)]),
                ("Impression", "impression", "select", True, [("Recto", "recto", 0), ("Recto-verso", "recto-verso", 4000)]),
                ("Finition", "finition", "select", True, [("Mat", "mat", 0), ("Brillant", "brillant", 2500), ("Soft touch", "soft-touch", 6000)]),
                ("Fichier design/logo", "fichier", "file", False, []),
            ],
            "flyers": [
                ("Format", "format", "select", True, [("A6", "a6", 0), ("A5", "a5", 2000), ("A4", "a4", 5000), ("A3", "a3", 9000)]),
                ("Quantite", "quantite", "select", True, [("100", "100", 0), ("250", "250", 7000), ("500", "500", 15000), ("1000", "1000", 28000)]),
                ("Papier", "papier", "select", True, [("Standard", "standard", 0), ("Premium", "premium", 3000), ("Mat", "mat", 4000)]),
                ("Fichier design/logo", "fichier", "file", False, []),
            ],
            "roll-up": [
                ("Format", "format", "select", True, [("85 x 200 cm", "85x200", 0), ("100 x 200 cm", "100x200", 6000)]),
                ("Structure", "structure", "select", True, [("Standard", "standard", 0), ("Premium", "premium", 9000)]),
                ("Fichier design/logo", "fichier", "file", False, []),
            ],
            "t-shirts-personnalises": [
                ("Taille", "taille", "select", True, [("S", "s", 0), ("M", "m", 0), ("L", "l", 0), ("XL", "xl", 1000), ("XXL", "xxl", 1500)]),
                ("Couleur", "couleur", "select", True, [("Blanc", "blanc", 0), ("Noir", "noir", 1000), ("Gris", "gris", 1000)]),
                ("Zone d'impression", "zone-impression", "select", True, [("Devant", "devant", 0), ("Dos", "dos", 0), ("Devant + dos", "devant-dos", 5000)]),
                ("Logo/image", "fichier", "file", False, []),
                ("Texte personnalise", "texte", "text", False, []),
            ],
            "mugs-personnalises": [
                ("Couleur", "couleur", "select", True, [("Blanc", "blanc", 0), ("Noir", "noir", 1000)]),
                ("Impression", "impression", "select", True, [("Une face", "une-face", 0), ("Deux faces", "deux-faces", 1500), ("Panorama", "panorama", 2500)]),
                ("Image/logo", "fichier", "file", False, []),
                ("Texte personnalise", "texte", "text", False, []),
            ],
            "stickers": [
                ("Format", "format", "select", True, [("Petit", "petit", 0), ("Moyen", "moyen", 2500), ("Grand", "grand", 5000)]),
                ("Quantite", "quantite", "select", True, [("50", "50", 0), ("100", "100", 3500), ("250", "250", 9000), ("500", "500", 16000)]),
                ("Matiere", "matiere", "select", True, [("Papier", "papier", 0), ("Vinyle", "vinyle", 4500), ("Transparent", "transparent", 6000)]),
                ("Fichier design/logo", "fichier", "file", False, []),
            ],
            "brochures-depliants": [
                ("Format", "format", "select", True, [("A5", "a5", 0), ("A4", "a4", 5000)]),
                ("Pli", "pli", "select", True, [("Simple", "simple", 0), ("Deux plis", "deux-plis", 3000), ("Trois plis", "trois-plis", 5000)]),
                ("Quantite", "quantite", "select", True, [("100", "100", 0), ("250", "250", 9000), ("500", "500", 18000)]),
                ("Fichier design/logo", "fichier", "file", False, []),
            ],
            "enveloppes-papier-entete": [
                ("Support", "support", "select", True, [("Papier entete", "papier-entete", 0), ("Enveloppes", "enveloppes", 2500), ("Pack complet", "pack-complet", 6000)]),
                ("Quantite", "quantite", "select", True, [("100", "100", 0), ("250", "250", 6000), ("500", "500", 12000)]),
                ("Fichier design/logo", "fichier", "file", False, []),
            ],
        }

        for product_slug, options in option_specs.items():
            product = Product.objects.get(slug=product_slug)
            ProductOption.objects.filter(product=product).exclude(
                code__in=[option[1] for option in options]
            ).delete()
            for option_index, (name, code, input_type, required, choices) in enumerate(options, start=1):
                option, _ = ProductOption.objects.update_or_create(
                    product=product,
                    code=code,
                    defaults={
                        "name": name,
                        "input_type": input_type,
                        "required": required,
                        "sort_order": option_index,
                    },
                )
                option.choices.exclude(value__in=[choice[1] for choice in choices]).delete()
                for choice_index, (label, value, price_delta) in enumerate(choices, start=1):
                    ProductOptionChoice.objects.update_or_create(
                        option=option,
                        value=value,
                        defaults={
                            "label": label,
                            "price_delta": price_delta,
                            "sort_order": choice_index,
                        },
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"SenPrinTech catalogue ready: {created_count} created, {updated_count} updated."
            )
        )
