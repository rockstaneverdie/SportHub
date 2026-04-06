from django.core.management.base import BaseCommand
from store.models import Category, Product


class Command(BaseCommand):
    help = 'Заполнить базу данных тестовыми данными'

    def handle(self, *args, **kwargs):
        # Категории
        categories_data = [
            ('Бег', 'running', '🏃'),
            ('Фитнес', 'fitness', '💪'),
            ('Велоспорт', 'cycling', '🚴'),
            ('Плавание', 'swimming', '🏊'),
            ('Командные виды', 'team-sports', '⚽'),
            ('Туризм', 'outdoor', '🏕️'),
        ]

        categories = {}
        for name, slug, icon in categories_data:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon})
            categories[slug] = cat
            self.stdout.write(f'  Категория: {name}')

        # Товары
        products_data = [
            # Бег
            ('Кроссовки Nike Air Zoom', 'nike-air-zoom', 'running', 24900, 29900, True, 15,
             'Профессиональные беговые кроссовки с технологией Air Zoom для максимального комфорта на длинных дистанциях. Идеальны для асфальта и грунта.'),
            ('Беговые шорты Adidas', 'adidas-run-shorts', 'running', 4900, None, False, 30,
             'Лёгкие шорты с встроенными тайтсами. Отводят влагу, не стесняют движений.'),
            ('Пульсометр Garmin Forerunner', 'garmin-forerunner', 'running', 34900, 39900, True, 8,
             'GPS-часы с пульсометром. Точно отслеживают темп, дистанцию и состояние организма.'),
            ('Компрессионные носки', 'compression-socks', 'running', 1290, None, False, 50,
             'Специальные носки для бега, снижающие усталость ног на длинных дистанциях.'),

            # Фитнес
            ('Гантели разборные 20 кг', 'dumbbells-20kg', 'fitness', 8900, 11900, True, 12,
             'Комплект разборных гантелей из чугуна с хромированными рукоятками. Регулировка от 2 до 20 кг.'),
            ('Коврик для йоги', 'yoga-mat', 'fitness', 2900, None, False, 40,
             'Нескользящий коврик из натурального каучука. Толщина 6 мм, размер 183×61 см.'),
            ('Фитнес-резинки набор', 'resistance-bands', 'fitness', 1990, 2500, False, 35,
             'Набор из 5 резинок разного сопротивления. Подходят для упражнений на всё тело.'),
            ('Пояс атлетический кожаный', 'lifting-belt', 'fitness', 5900, None, True, 10,
             'Широкий кожаный пояс для тяжёлой атлетики. Надёжная поддержка поясницы.'),

            # Велоспорт
            ('Шлем велосипедный Scott', 'scott-helmet', 'cycling', 8900, 10900, True, 7,
             'Аэродинамический шлем с 18 вентиляционными каналами. Сертификат CE EN 1078.'),
            ('Велоперчатки GEL', 'cycling-gloves', 'cycling', 2490, None, False, 25,
             'Перчатки с гелевыми вставками. Защита ладоней, улучшенный хват руля.'),
            ('Велокомпьютер Sigma', 'sigma-computer', 'cycling', 4900, 5900, False, 14,
             'Беспроводной велокомпьютер. 14 функций, водонепроницаемый, большой дисплей.'),

            # Плавание
            ('Очки для плавания Speedo', 'speedo-goggles', 'swimming', 2900, 3500, True, 20,
             'Профессиональные очки с антизапотевающим покрытием и UV-защитой. Регулируемая переносица.'),
            ('Шапочка силиконовая', 'swim-cap', 'swimming', 890, None, False, 45,
             'Прочная силиконовая шапочка. Не тянет волосы, подходит для тренировок и соревнований.'),
            ('Плавательная доска', 'kickboard', 'swimming', 1490, None, False, 18,
             'Доска для отработки удара ног. EVA-пена, эргономичная форма.'),

            # Командные виды
            ('Мяч футбольный Adidas', 'adidas-football', 'team-sports', 3900, 4900, True, 22,
             'Официальный мяч FIFA Quality. Ручная прошивка, бутиловая камера, стабильная форма.'),
            ('Баскетбольный мяч Spalding', 'spalding-basketball', 'team-sports', 4900, None, False, 16,
             'Профессиональный баскетбольный мяч размер 7. Отличное сцепление с поверхностью.'),

            # Туризм
            ('Рюкзак туристический 60L', 'hiking-backpack-60', 'outdoor', 12900, 15900, True, 9,
             'Вместительный рюкзак с алюминиевой рамой и поясным ремнём. Дождевой чехол в комплекте.'),
            ('Спальный мешок -10°C', 'sleeping-bag', 'outdoor', 8900, None, True, 11,
             'Трёхсезонный спальник на синтетическом утеплителе. Температура комфорта -10°C, вес 1.2 кг.'),
            ('Трекинговые палки', 'trekking-poles', 'outdoor', 3900, 4900, False, 20,
             'Алюминиевые складные палки с пробковыми ручками и ремешками для запястий.'),
        ]

        for name, slug, cat_slug, price, old_price, featured, stock, desc in products_data:
            Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': categories[cat_slug],
                    'price': price,
                    'old_price': old_price,
                    'is_featured': featured,
                    'stock': stock,
                    'description': desc,
                }
            )
            self.stdout.write(f'  Товар: {name}')

        self.stdout.write(self.style.SUCCESS('\n✅ База данных успешно заполнена!'))
