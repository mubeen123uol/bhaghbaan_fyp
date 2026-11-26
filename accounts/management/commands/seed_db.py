from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from accounts.models import User, SellerProfile
from plants.models import Plant, Disease, Treatment
from services.models import Garden, GardenMember, Task, TaskReport, Expense
from marketplace.models import Product, CommissionSetting
from community.models import Group, GroupMembership, ChatRoom, Message
from care.models import UserPlant
from care.services import CareCalendarService
from ai_doctor.models import AISetting

class Command(BaseCommand):
    help = 'Seeds database with realistic Pakistani plants, diseases, users, gardens, tasks, and marketplace catalog.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Baghbaan AI comprehensive database seeding..."))

        # 0. AI Settings & Commission Settings
        AISetting.objects.get_or_create(
            id=1,
            defaults={'confidence_threshold': 60.0, 'daily_quota_limit': 1000, 'provider_priority': 'PLANT_ID_THEN_GEMINI'}
        )
        CommissionSetting.objects.get_or_create(
            id=1,
            defaults={'commission_percentage': 5.0, 'is_active': True}
        )

        # 1. Users
        self.stdout.write("Seeding user accounts across all roles...")
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@baghbaan.pk',
                'role': 'ADMIN',
                'first_name': 'Super',
                'last_name': 'Admin',
                'city': 'Lahore',
                'latitude': Decimal('31.5204'),
                'longitude': Decimal('74.3587'),
                'is_staff': True,
                'is_superuser': True,
                'preferred_language': 'ur'
            }
        )
        admin.set_password('admin123')
        admin.save()

        homeowner, _ = User.objects.get_or_create(
            username='ahmed',
            defaults={
                'email': 'ahmed@gmail.com',
                'role': 'HOMEOWNER',
                'first_name': 'احمد',
                'last_name': 'خان',
                'phone': '03001234567',
                'city': 'Lahore',
                'latitude': Decimal('31.5204'),
                'longitude': Decimal('74.3587'),
                'preferred_language': 'ur',
                'bio': 'ماڈل ٹاؤن لاہور میں گھر کی چھت پر کچن گارڈننگ کا شوقین ہوں۔'
            }
        )
        homeowner.set_password('password123')
        homeowner.save()

        gardener, _ = User.objects.get_or_create(
            username='ali_mali',
            defaults={
                'email': 'ali.mali@gmail.com',
                'role': 'GARDENER',
                'first_name': 'علی',
                'last_name': 'مالی',
                'phone': '03219876543',
                'city': 'Lahore',
                'latitude': Decimal('31.5150'),
                'longitude': Decimal('74.3450'),
                'is_verified_professional': True,
                'years_of_experience': 8,
                'hourly_rate': Decimal('500.00'),
                'preferred_language': 'ur',
                'bio': 'لاہور میں گھریلو باغات کی کانٹ چھانٹ، لان کی کٹائی اور کھاد ڈالنے کا 8 سالہ تجربہ۔'
            }
        )
        gardener.set_password('password123')
        gardener.save()

        supervisor, _ = User.objects.get_or_create(
            username='tariq_supervisor',
            defaults={
                'email': 'tariq.horticulture@gmail.com',
                'role': 'SUPERVISOR',
                'first_name': 'طارق',
                'last_name': 'محمود',
                'phone': '03335554433',
                'city': 'Lahore',
                'latitude': Decimal('31.5300'),
                'longitude': Decimal('74.3600'),
                'is_verified_professional': True,
                'years_of_experience': 15,
                'hourly_rate': Decimal('1200.00'),
                'preferred_language': 'ur',
                'bio': 'زرعی یونیورسٹی فیصل آباد سے ہارٹیکلچر میں گریجویٹ، بڑے باغات کا معائنہ کار۔'
            }
        )
        supervisor.set_password('password123')
        supervisor.save()

        seller_user, _ = User.objects.get_or_create(
            username='bilal_nursery',
            defaults={
                'email': 'bilal.nursery@gmail.com',
                'role': 'SELLER',
                'first_name': 'بلال',
                'last_name': 'نرسری والے',
                'phone': '03456789012',
                'city': 'Lahore',
                'latitude': Decimal('31.5050'),
                'longitude': Decimal('74.3350'),
                'preferred_language': 'ur',
                'bio': 'گلبرگ ماڈل نرسری لاہور، تمام اقسام کے دیسی و غیر ملکی پودوں اور نامیاتی کھاد کے سپلائر۔'
            }
        )
        seller_user.set_password('password123')
        seller_user.save()

        seller_profile, _ = SellerProfile.objects.get_or_create(
            user=seller_user,
            defaults={
                'business_name': 'گلبرگ گرین نرسری (Gulberg Green Nursery)',
                'cnic_number': '35202-1234567-1',
                'shop_address': 'مین بلیوارڈ، گلبرگ 3، بالمقابل قذافی اسٹیڈیم، لاہور',
                'contact_phone': '03456789012',
                'verification_status': 'VERIFIED',
                'admin_notes': 'نرسری کی فزیکل تصدیق مکمل ہو چکی ہے۔ تمام کوالٹی معیارات درست ہیں۔'
            }
        )

        # 2. Curated Pakistani Plants (60+ Botanical Profiles)
        self.stdout.write("Seeding 60+ Pakistani indigenous and common home garden plants...")
        plants_data = [
            # Ornamental / Flowers
            ("Desi Gulab (Rose)", "دیسی گلاب", "Desi Gulab", "Rosa damascena", "ORNAMENTAL",
             "Fragrant red/pink flower deeply cherished in Pakistani homes and courtyards.",
             "خوشبودار سرخ و گلابی دیسی پھول جو پاکستانی گھروں، صحنوں اور چھتوں میں بکثرت لگایا جاتا ہے۔ عرق گلاب کی تیاری میں مفید ہے۔",
             2, 25, "Winter (January)", "Full Sun", False, "Thrives in Punjab and Sindh during winter and spring; protect from scorching June heat."),
            
            ("Motia / Jasmine", "موتیا / چنبیلی", "Motia", "Jasminum sambac", "ORNAMENTAL",
             "White fragrant blossom and national pride of Pakistan, popular for garlands.",
             "سفید خوشبودار پھول جو شام کے وقت مہکتا ہے۔ گرمیوں میں تیزی سے پھلتا پھولتا ہے۔ گجروں اور ہار بنانے میں عام استعمال ہوتا ہے۔",
             2, 30, "Late Autumn", "Full Sun", False, "Summer flowering plant that requires rich well-draining soil."),
            
            ("Chameli / Spanish Jasmine", "چمبیلی (قومی پھول)", "Chameli", "Jasminum officinale", "ORNAMENTAL",
             "The National Flower of Pakistan, elegant climbing creeper with starry white petals.",
             "پاکستان کا قومی پھول، سفید پنکھڑیوں والی خوبصورت بیل جو دیواروں اور جالیوں پر خوب چڑھتی ہے۔",
             2, 30, "Monsoon", "Full Sun to Partial Shade", False, "National flower, hardy across all provinces of Pakistan."),

            ("Money Plant", "منی پلانٹ", "Money Plant", "Epipremnum aureum", "INDOOR",
             "Heart-shaped hardy climber suitable for indoor jars, balconies, and water pots.",
             "دل کی شکل کے پتوں والی سدا بہار بیل۔ گھر کے اندر، پانی کی بوتلوں اور بالکونی کے گملوں میں آسانی سے اگتی ہے۔",
             3, 45, "Spring", "Partial Shade to Low Light", True, "Avoid direct harsh sunlight in Pakistani summers to prevent leaf scorching."),

            ("Raat ki Rani", "رات کی رانی", "Raat ki Rani", "Cestrum nocturnum", "ORNAMENTAL",
             "Night-blooming jasmine that perfumes entire neighbourhoods after dark.",
             "رات کے وقت مسحور کن خوشبو بکھیرنے والی مشہور جھاڑی۔ اس کے سفید و ہلکے سبز پھول رات کو کھلتے ہیں۔",
             2, 30, "Monsoon", "Full Sun", False, "Requires moderate watering and regular trimming after flowering."),

            ("Sada Bahar / Periwinkle", "سدا بہار", "Sada Bahar", "Catharanthus roseus", "ORNAMENTAL",
             "Tough, continuous flowering shrub that tolerates harsh heat and drought.",
             "شدید گرمی اور کم پانی کو برداشت کرنے والا سدا بہار پودا جو سال بھر گلابی اور سفید پھول دیتا ہے۔",
             3, 60, "Anytime", "Full Sun", False, "Extremely resilient in Karachi, Lahore, and Multan urban environments."),

            ("Bougainvillea", "بوگن ویلیا", "Bouganvilla", "Bougainvillea spectabilis", "ORNAMENTAL",
             "Vibrant pink, purple, and orange climbing shrub adorning city fences.",
             "روشن گلابی، جامنی اور نارنجی پتوں نما پھولوں والی بیل جو پاکستانی گیٹوں اور دیواروں کی زینت بنتی ہے۔",
             4, 60, "Post-Monsoon", "Full Sun", False, "Drought tolerant; overwatering reduces flowering."),

            ("Zard Kaner / Oleander", "زرد کنیر", "Zard Kaner", "Cascabela thevetia", "ORNAMENTAL",
             "Hardy roadside shrub with bright yellow trumpet flowers.",
             "پیلے پھولوں والی سخت جان جھاڑی جو کم پانی اور سخت گرمی میں بھی شاداب رہتی ہے۔",
             4, 60, "Spring", "Full Sun", False, "Drought resistant, leaves are poisonous if consumed by pets."),

            ("Genda / Marigold", "گیندا", "Genda", "Tagetes erecta", "ORNAMENTAL",
             "Festive yellow and orange winter annual, repels garden pests naturally.",
             "موسم سرما کا خوبصورت اور روایتی پیلا پھول۔ یہ پودا قدرتی طور پر مٹی کے نقصان دہ کیڑوں کو دور رکھتا ہے۔",
             2, 20, "Autumn", "Full Sun", False, "Winter essential for Pakistani roof-tops and garden beds."),

            ("Petunia", "پیٹونیا", "Petunia", "Petunia hybrida", "ORNAMENTAL",
             "Vibrant funnel-shaped winter bedding annual in countless color hues.",
             "سردیوں کا مقبول پھول جو نومبر سے اپریل تک گملوں اور کیاریوں کو رنگین رکھتا ہے۔",
             2, 15, "None", "Full Sun", False, "Requires frequent feeding during peak winter bloom."),

            ("Gul-e-Dawoodi / Chrysanthemum", "گل داؤدی", "Gul-e-Dawoodi", "Chrysanthemum morifolium", "ORNAMENTAL",
             "The celebrated monarch of Pakistani winter flower shows, bursting in magnificent multi-colored blooms.",
             "پاکستان میں موسم خزاں اور سرما کا سب سے بڑا روایتی نمائش کا پھول۔ سینکڑوں اقسام اور رنگوں میں دل موہ لیتا ہے۔",
             2, 15, "Post-flowering (Feb)", "Full Sun", False, "Pinch growing tips until September to create bushy domes loaded with flower buds."),

            ("Dahlia", "ڈاہلیا (شاہانہ پھول)", "Dahlia", "Dahlia pinnata", "ORNAMENTAL",
             "Spectacular giant dinner-plate blooms in dazzling scarlet, crimson, and dual-tone hues for winter borders.",
             "موسم سرما کا دیوہیکل اور شاہانہ پھول جس کی گہری رنگت اور بڑی پنکھڑیاں ہر دیکھنے والے کو مسحور کر دیتی ہیں۔",
             2, 15, "None", "Full Sun", False, "Stake tall flower stems securely against strong winter gusts and feed with potash."),

            ("Gazania", "گزانیہ (سورج مکھی نما)", "Gazania", "Gazania rigens", "ORNAMENTAL",
             "Brilliant daisy-like blooms with eye-catching ring patterns that open wide in dazzling Pakistani sunshine.",
             "سورج کی روشنی میں کھلنے والا انتہائی روشن پھول جو کم پانی اور سخت دھوپ میں بھی کیاریوں کو قالین بنا دیتا ہے۔",
             3, 30, "None", "Full Direct Sun", False, "Flowers close at sunset and on cloudy days; excellent for rooftop pots and borders."),

            ("Geranium", "جیرانیم (عطری پھول)", "Geranium", "Pelargonium hortorum", "ORNAMENTAL",
             "Ever-blooming container favourite with velvety scalloped leaves and vivid clusters of coral and red petals.",
             "گملوں اور بالکونیوں کا سدا بہار ساتھی جس کے خوبصورت سرخ، گلابی اور نارنجی گچھے مہینوں کھلے رہتے ہیں۔",
             3, 25, "Spring", "Full Sun to Partial Afternoon Shade", False, "Avoid wetting leaves while watering; deadhead faded flower stems to spur fresh buds."),

            ("Hybrid Sadabahar", "ہائبرڈ سدا بہار", "Hybrid Sadabahar", "Catharanthus roseus nanus", "ORNAMENTAL",
             "Dwarf heat-tolerant miracle flower continuously blooming under blazing 45°C Punjab summer sun.",
             "شدید ترین گرمی اور لو میں بھی بغیر رکے پھول دینے والا بونا پودا جو گملوں میں رنگ برنگے قالین بچھا دیتا ہے۔",
             3, 45, "Anytime", "Full Sun", False, "Requires zero maintenance; thrives on neglect in well-draining garden soil."),

            # Indoor Air Purifiers & Houseplants
            ("Snake Plant / Sansevieria", "سانپ پودا (سنسویریا)", "Snake Plant", "Sansevieria trifasciata", "INDOOR",
             "Indestructible architectural succulent that releases oxygen at night and filters toxic airborne pollutants.",
             "انتہائی سخت جان انڈور پودا جو رات کے وقت آکسیجن خارج کرتا ہے اور ہوا سے نقصان دہ زہریلی گیسوں کو صاف کرتا ہے۔ کم پانی میں بھی سالوں شاداب رہتا ہے۔",
             10, 60, "None", "Low to Bright Indirect Light", True, "Top NASA air purifier; overwatering causes root rot, keep soil mostly dry in winter."),

            ("Spider Plant / Chlorophytum", "مکڑی پودا (مکڑی بیل)", "Spider Plant", "Chlorophytum comosum", "INDOOR",
             "Air-purifying hanging plant with arching green-and-white striped leaves producing baby plantlets.",
             "خوبصورت دھاری دار پتوں والا پودا جس سے چھوٹے ننھے پودے لٹکتے ہیں۔ کمرے کی ہوا سے کاربن مونو آکسائیڈ اور زہریلے مادے جذب کرتا ہے۔",
             4, 30, "Spring", "Bright Indirect Light", True, "Safe for cats and dogs; thrives in drawing rooms and shaded balconies across Pakistan."),

            ("Peace Lily", "پیس للی (امن کا پھول)", "Peace Lily", "Spathiphyllum wallisii", "INDOOR",
             "Glossy dark green leaves with graceful pure white spathes that bloom indoors in low light.",
             "گہرے سبز چمکدار پتوں اور پرسکون سفید پھولوں والا اندرونی پودا جو نمی اور ٹھنڈک پسند کرتا ہے۔ کمرے کی فضا کو تروتازہ رکھتا ہے۔",
             3, 30, "Post-bloom", "Low to Medium Indirect Light", True, "Droops noticeably when thirsty; instantly perks up after a refreshing drink."),

            ("Areca Palm", "اریکا پام", "Areca Palm", "Dypsis lutescens", "INDOOR",
             "Lush feathery tropical palm that humidifies dry indoor air and adds luxury aesthetics to rooms.",
             "گھنے پروں جیسے پتوں والا خوبصورت پام جو پاکستانی ڈرائنگ رومز اور برآمدوں کو سرسبز بناتا ہے اور خشک ہوا میں قدرتی نمی لاتا ہے۔",
             3, 30, "Spring", "Bright Filtered Light", True, "Needs well-draining potting mix and misting during dry hot summer months in Punjab."),

            ("Fiddle Leaf Fig", "فڈل لیف فگ", "Fiddle Leaf Fig", "Ficus lyrata", "INDOOR",
             "High-end architectural plant boasting dramatic broad violin-shaped leaves for modern interiors.",
             "وائلن کی شکل کے بڑے اور پرکشش پتوں والا شاندار پودا جو جدید گھروں کے اندرونی حصوں کی خوبصورتی میں بے پناہ اضافہ کرتا ہے۔",
             5, 45, "Spring", "Bright Indirect Light", True, "Wipe broad leaves monthly with a damp cotton cloth to remove urban dust deposits."),

            ("Golden Pothos / Marble Queen", "ماربل کوئین منی پلانٹ", "Marble Queen Pothos", "Epipremnum aureum 'Marble Queen'", "INDOOR",
             "Striking white and green marbled variegation on heart-shaped climbing and cascading foliage.",
             "سفید اور سبز رنگ کے سنگ مرمر جیسے دلکش پتوں والی بیل جو بالکونیوں اور کمروں کی جالیوں پر خوبصورت نظر آتی ہے۔",
             4, 30, "Summer", "Bright Indirect Light", True, "Higher light preserves rich white variegation; highly resilient in local soils."),

            # Succulents & Drought Tolerant
            ("Aloe Vera / Ghee Kawar", "ایلوویرا (گھیگوار)", "Aloe Vera", "Aloe barbadensis miller", "SUCCULENT",
             "Succulent with medicinal gel for skin burns, hair care, and digestion.",
             "موٹے گودے دار پتوں والا سخت جان پودا جس کا جیل جلد کی خوبصورتی، جلنے اور بالوں کے لیے لاجواب ہے۔",
             7, 90, "None", "Indirect Bright Sun", True, "Overwatering kills Aloe Vera; let soil dry completely between waterings."),

            ("Jade Plant / Lucky Plant", "جیڈ پلانٹ (لکی منی ٹری)", "Jade Plant", "Crassula ovata", "SUCCULENT",
             "Fleshy oval emerald leaves on woody stems, symbolizing enduring prosperity and good fortune.",
             "گودے دار گول پتوں اور لکڑی نما تنے والا پودا جسے برکت اور خوشحالی کی علامت سمجھا جاتا ہے۔ انتہائی کم دیکھ بھال مانگتا ہے۔",
             7, 60, "Prune tips", "Bright Direct to Indirect Sun", True, "Drought resilient; allow soil to dry out between waterings to prevent soft stems."),

            ("Adenium / Desert Rose", "صحرائی گلاب (ایڈینیم)", "Adenium / Desert Rose", "Adenium obesum", "SUCCULENT",
             "Bonsai-like swollen succulent trunk crowned with dazzling bell-shaped pink and ruby blooms.",
             "موٹے تنے اور شاندار شوخ گلابی و سرخ پھولوں والا صحرائی پودا جو شدید گرمی اور تیز دھوپ کا عاشق ہے۔",
             6, 45, "Late Winter", "Full Direct Sun", False, "Requires gritty sand-rich soil with zero water stagnation; reduce water to minimum in winter."),

            ("Kalanchoe", "کلانچو", "Kalanchoe", "Kalanchoe blossfeldiana", "SUCCULENT",
             "Compact winter-flowering succulent bearing vibrant dense clusters of red, orange, and yellow blooms.",
             "سردیوں میں کھلنے والا پرکشش پودا جو گچھوں کی صورت میں شوخ سرخ، پیلے اور گلابی پھول دیتا ہے جو مہینوں تازہ رہتے ہیں۔",
             5, 30, "Post-flowering", "Bright Sunlight", True, "Perfect tabletop succulent; water only when the top two inches of soil feel dry."),

            # Herbs & Kitchen Greens
            ("Pudina / Mint", "پودینہ", "Pudina", "Mentha spicata", "HERB",
             "Fragrant kitchen herb used everyday in Pakistani chutneys and refreshing drinks.",
             "پاکستانی کھانوں، چٹنیوں اور رائتے کا لازمی جزو۔ ہلکی نمی اور جزوی دھوپ میں تیزی سے پھیلتا ہے۔",
             1, 15, "Spring", "Partial Shade", True, "Moisture loving, best harvested frequently to promote bushy green leaves."),

            ("Dhaniya / Coriander", "دھنیا", "Dhaniya", "Coriandrum sativum", "HERB",
             "Staple green herb garnishing virtually every Pakistani curry and dish.",
             "سالن اور ہنڈیا کا لازمی حصہ۔ سرما اور بہار میں بیجوں سے گملوں میں انتہائی آسانی سے اگایا جا سکتا ہے۔",
             1, 20, "Harvest Regularly", "Full Sun to Partial Shade", False, "Cool-season crop; bolts quickly in high summer heat."),

            ("Kari Patta / Curry Leaf", "کڑی پتہ", "Kari Patta", "Murraya koenigii", "HERB",
             "Aromatic culinary shrub whose fresh leaflets season lentils, curries, and dals.",
             "خوشبودار پتوں والا پودا جس کا تڑکا دالوں اور سبزیوں میں ذائقہ پیدا کرتا ہے۔ گملوں میں بہت اچھا اگتا ہے۔",
             2, 30, "Monsoon", "Full Sun", False, "Sensitive to winter frost; shelter under a porch in December/January in Punjab."),

            ("Tulsi / Holy Basil", "تلسی / نیازبو", "Tulsi / Niazbo", "Ocimum tenuiflorum", "HERB",
             "Sacred and medicinal aromatic herb with insect-repellent properties.",
             "طبی اور خوشبودار پودا جو مچھروں اور کیڑوں کو قدرتی طور پر بھگاتا ہے۔ چائے اور قہوے میں بھی استعمال ہوتا ہے۔",
             2, 30, "Spring", "Full Sun", False, "Prune flower heads to keep leaf foliage dense and aromatic."),

            ("Adrak / Ginger", "ادرک", "Adrak", "Zingiber officinale", "HERB",
             "Underground aromatic rhizome cultivated in moist, shaded garden planters.",
             "کھانوں اور قہووں میں روزانہ استعمال ہونے والی جڑ۔ نرم بھل والی مٹی اور جزوی چھاؤں میں اچھی اگتی ہے۔",
             2, 30, "Monsoon", "Partial Shade", False, "Harvest after 8-10 months when leaves turn yellow."),

            ("Ajwain Leaf / Mexican Mint", "اجوائن کا پتہ (کولیس)", "Ajwain Leaf", "Coleus amboinicus", "HERB",
             "Thick velvety succulent leaf with intense aromatic thyme/carom scent, used in pakoras and herbal teas.",
             "موٹے رسیلے اور خوشبودار پتوں والا گھریلو طبی پودا جس کے پکوڑے لذیذ بنتے ہیں اور قہوہ کھانسی و پیٹ درد میں فوری آرام دیتا ہے۔",
             3, 40, "Spring", "Partial Shade", True, "Propagates instantly from stem cuttings inserted in moist sandy loam."),

            ("Lemongrass", "لیمن گراس (لیموں گھاس)", "Lemongrass", "Cymbopogon citratus", "HERB",
             "Fast-clumping tropical grass with invigorating citrus aroma; essential for herbal green tea.",
             "تیزی سے پھیلنے والی خوشبودار لیموں گھاس جس کا سبز قہوہ ہاضمے اور وزن کم کرنے کے لیے دنیا بھر میں مشہور ہے۔",
             2, 30, "Monsoon", "Full Sun to Partial Shade", False, "Cut leaves regularly to encourage fresh tender aromatic stalks."),

            ("Kasuri Methi", "قصوری میتھی", "Kasuri Methi", "Trigonella foenum-graecum", "HERB",
             "Legendary fragrant winter herb from Kasur, Punjab, conferring heavenly aroma to Pakistani curries.",
             "پنجاب کے تاریخی شہر قصور کی عالمی شہرت یافتہ خوشبودار میتھی جو سالن، پراٹھوں اور ساگ کی جان ہے۔",
             2, 20, "Cut and regrow", "Full Sun", False, "Sow seeds in cool October breeze; multiple cuttings throughout cold winter months."),

            ("Saunf / Sweet Fennel", "سونف کا پودا", "Saunf", "Foeniculum vulgare", "HERB",
             "Graceful feathery aromatic herb producing sweet edible stalks and medicinal digestion-boosting seeds.",
             "سردیوں کی خوبصورت جڑی بوٹی جس کے نرم پتے سلاد میں اور بیج کھانوں کے بعد ہاضمے اور ٹھنڈک کے لیے استعمال ہوتے ہیں۔",
             3, 30, "Spring", "Full Sun", False, "Attracts beneficial pollinators and predatory wasps to protect the garden."),

            # Vegetables & Kitchen Garden
            ("Tamatar / Tomato", "ٹماٹر", "Tamatar", "Solanum lycopersicum", "VEGETABLE",
             "The king of Pakistani kitchen gardens; delicious fruit for salans and salads.",
             "گھریلو کچن گارڈننگ کی سب سے مقبول سبزی۔ گملوں اور گرو بیگز میں وافر مقدار میں پھل دیتی ہے۔",
             2, 20, "Pinch suckers", "Full Sun", False, "Requires staking support and calcium-rich soil to prevent blossom end rot."),

            ("Hari Mirch / Green Chilli", "ہری مرچ", "Hari Mirch", "Capsicum annuum", "VEGETABLE",
             "Fiery spicy peppers grown in pots on every Pakistani rooftop.",
             "تیز تیکھی مرچیں جو چھوٹے گملے میں بھی سینکڑوں مرچیں پیدا کرتی ہیں۔ گھریلو استعمال کے لیے بہترین ہے۔",
             2, 25, "Spring", "Full Sun", False, "Loves warm weather; water moderately when flowering starts."),

            ("Baingan / Eggplant", "بینگن", "Baingan", "Solanum melongena", "VEGETABLE",
             "Glossy purple fruit thriving in warm Pakistani monsoon and summer seasons.",
             "چمکدار جامنی سبزی جو گرمیوں اور برسات میں خوب پھلتی ہے۔ اس کے لیے گہرا غملا درکار ہوتا ہے۔",
             2, 25, "Summer", "Full Sun", False, "Heavy feeder; enrich soil with compost or well-rotted cow dung."),

            ("Palak / Spinach", "پالک", "Palak", "Spinacia oleracea", "VEGETABLE",
             "Nutrient-dense iron-rich leafy green, harvestable multiple times in winter.",
             "سردیوں کی ہر دلعزیز سبزی۔ بیج ڈالنے کے صرف چار ہفتوں بعد پتے کاٹنے کے قابل ہو جاتے ہیں۔",
             2, 20, "Cut and come again", "Full Sun to Partial Shade", False, "Cut outer leaves, and the plant regrows multiple times."),

            ("Desi Palak / Broadleaf Spinach", "دیسی پالک (چوڑے پتے)", "Desi Palak", "Spinacia oleracea 'Desi'", "VEGETABLE",
             "Fast-growing broadleaf green, packed with iron and calcium.",
             "سردیوں کی غذائیت سے بھرپور دیسی پالک جس کے چوڑے پتے ہر دو ہفتے بعد دوبارہ اگتے ہیں۔",
             2, 15, "Cut outer leaves", "Full Sun to Partial Shade", False, "Harvest outer leaves with sharp kitchen scissors."),

            ("Bhindi / Okra (Ladyfinger)", "بھنڈی", "Bhindi", "Abelmoschus esculentus", "VEGETABLE",
             "Popular summer vegetable producing tender green pods loved by Pakistani families.",
             "موسم گرما اور برسات کی مشہور و پسندیدہ سبزی۔ تیز گرمی اور دھوپ میں خوب پھل دیتی ہے۔",
             2, 25, "Monsoon", "Full Sun", False, "Sow seeds from March to June for continuous summer harvest."),

            ("Kheera / Cucumber", "کھیرا", "Kheera", "Cucumis sativus", "VEGETABLE",
             "Refreshing salad vine climbing trellis netting in spring and monsoon.",
             "سلاد کا بادشاہ، گرمیوں میں ٹھنڈک پہنچانے والی بیل جو جالی پر چڑھ کر خوب پھل لاتی ہے۔",
             1, 20, "Pinch tips", "Full Sun", False, "Requires constant soil moisture to prevent bitter taste."),

            ("Shimla Mirch / Bell Pepper", "شملہ مرچ", "Shimla Mirch", "Capsicum annuum grossum", "VEGETABLE",
             "Crisp green and red bell peppers ideal for Chinese rice and stir-fries.",
             "سلاد اور چائنیز کھانوں میں پسند کی جانے والی خستہ مرچ۔ موسم سرما میں گملوں میں خوب اگتی ہے۔",
             2, 25, "Spring", "Full Sun", False, "Protect delicate fruits from harsh monsoon storms."),

            ("Mooli / Radish", "مولی", "Mooli", "Raphanus sativus", "VEGETABLE",
             "Crisp winter root vegetable eaten fresh with parathas and lime juice.",
             "سردیوں کے موسم کی خستہ سفید مولی، گملوں میں 40 دنوں میں تیار ہو جاتی ہے۔ پراٹھوں کے ساتھ پسندیدہ۔",
             3, 20, "None", "Full Sun", False, "Requires deep, loose sand-mixed soil for straight roots."),

            ("Gajar / Desi Red Carrot", "دیسی لال گاجر", "Desi Gajar", "Daucus carota", "VEGETABLE",
             "Deep-red sweet winter carrot used in famous Pakistani Gajar ka Halwa.",
             "پاکستانی سرخ و میٹھی گاجر جس کا حلوہ اور جوس سردیوں کی سوغات ہے۔ نرم مٹی میں خوب پھلتی ہے۔",
             3, 25, "Thin seedlings", "Full Sun", False, "Sow in October/November in loose bhal soil."),

            ("Karela / Bitter Gourd", "کریلا", "Karela", "Momordica charantia", "VEGETABLE",
             "Climbing vegetable packed with medicinal anti-diabetic compounds.",
             "شوگر کے مریضوں کے لیے مفید اور لذیذ سبزی۔ گرمیوں میں اس کی بیل تیزی سے پھیلتی ہے۔",
             2, 25, "Summer", "Full Sun", False, "Train over overhead trellises for pest-free hanging gourds."),

            ("Tori / Ridge Gourd", "توری", "Tori", "Luffa acutangula", "VEGETABLE",
             "Light, easily digestible summer gourd ideal for high heat conditions.",
             "گرمیوں کی ہلکی اور ہاضم سبزی، برسات کے موسم میں تیزی سے بڑھنے والی بیل۔",
             2, 30, "Monsoon", "Full Sun", False, "Needs trellis support and ample organic compost."),

            ("Lehsan / Garlic", "لہسن", "Lehsan", "Allium sativum", "VEGETABLE",
             "Pungent winter bulb that doubles as a companion plant repelling pests.",
             "سرما کی مشہور فصل۔ گملوں میں لونگیں دبا کر آسانی سے اگایا جاتا ہے، کیڑوں کو دور بھگاتا ہے۔",
             3, 30, "Winter", "Full Sun", False, "Plant cloves in October/November for a bountiful April harvest."),

            # Fruit Trees & Saplings
            ("Amrood / Guava", "امرود", "Amrood", "Psidium guajava", "FRUIT",
             "Beloved local fruit tree bearing sweet aromatic fruit twice a year.",
             "پاکستان کا مشہور و لذیذ پھل جو سال میں دو بار (سردیوں اور برسات) بھرپور پھل دیتا ہے۔",
             3, 45, "Post-harvest", "Full Sun", False, "Extremely well adapted to Punjab and Sindh soils."),

            ("Kagzi Nimbu / Lemon", "کاغذی لیموں", "Kaghzi Nimbu", "Citrus limon", "FRUIT",
             "Essential potted citrus providing fresh sour lemons year-round.",
             "گھریلو گملوں اور کیاریوں کے لیے بہترین لیموں کا پودا جو سارا سال رس دار لیموں فراہم کرتا ہے۔",
             3, 30, "Spring", "Full Sun", False, "Feed with micronutrients (zinc/iron) if leaves show yellowing veins."),

            ("Anar / Pomegranate", "انار", "Anar", "Punica granatum", "FRUIT",
             "Hardy fruit shrub yielding ruby-red antioxidant-rich arils.",
             "قندھاری اور دیسی انار، کم پانی میں بھی خوب پھلتا ہے اور اس کے سرخ پھول نہایت دلکش ہوتے ہیں۔",
             4, 60, "Winter", "Full Sun", False, "Tolerates high summer temperatures and alkaline soils."),

            ("Aam / Mango (Chaunsa/Anwar Ratol)", "آم کا پودا", "Aam", "Mangifera indica", "FRUIT",
             "The National Fruit of Pakistan; graft saplings grow well in home ground corners.",
             "پھلوں کا بادشاہ اور پاکستان کا قومی پھل۔ پیوندی پودے 3 سے 4 سال میں میٹھے آم دینا شروع کر دیتے ہیں۔",
             4, 45, "Post-Monsoon", "Full Sun", False, "King of Pakistani fruits; protect young sapling trunks from winter frost."),

            ("Shahtoot / Mulberry", "شہتوت", "Shahtoot", "Morus nigra", "FRUIT",
             "Sweet, juicy dark purple long berries ripening in early spring.",
             "موسم بہار میں میٹھے اور رسیلے شہتوت پیدا کرنے والا تیزی سے بڑھنے والا درخت۔",
             4, 60, "Winter", "Full Sun", False, "Birds love this tree; prune annually to maintain domestic garden height."),

            ("Injeer / Fig", "انجیر", "Injeer", "Ficus carica", "FRUIT",
             "Ancient sweet fruit mentioned in holy scriptures, grows exceptionally in containers.",
             "غذائیت اور برکتوں سے بھرپور پھل جو بڑے گملے میں بھی باآسانی میٹھے انجیر پیدا کرتا ہے۔",
             3, 45, "Winter", "Full Sun", False, "Very easy to propagate from hardwood cuttings."),

            ("Cheeku / Sapodilla", "چیکو", "Cheeku", "Manilkara zapota", "FRUIT",
             "Brown sweet caramel-tasting fruit tree that loves coastal and humid climates.",
             "شکر کے ذائقے جیسا میٹھا پھل، کراچی اور ساحلی علاقوں کی آب و ہوا میں شاندار پھلتا ہے۔",
             4, 60, "Post-harvest", "Full Sun", False, "Evergreen foliage with great resistance to wind."),

            ("Sindh Golden Chikoo", "سندھ گولڈن چیکو", "Sindh Golden Chikoo", "Manilkara zapota 'Sindh Golden'", "FRUIT",
             "Coastal and southern plain sapodilla producing honey-sweet brown fruits.",
             "سندھ اور زیریں پنجاب کا پسندیدہ پھل دار درخت جس کے میٹھے اور ذائقے دار چیکو سال میں دو بار تیار ہوتے ہیں۔",
             4, 45, "Post-harvest", "Full Sun", False, "Loves humid warm climate; requires organic compost top-dressing twice yearly."),

            ("Falsa", "فالسہ", "Falsa", "Grewia asiatica", "FRUIT",
             "Tangy cooling purple summer berries used for iconic Pakistani summer sherbets.",
             "گرمیوں کی شدت توڑنے والا ترش و میٹھا پھل جس کا شربت پاکستان بھر میں مقبول ہے۔",
             3, 45, "Severe Winter Pruning", "Full Sun", False, "Hard winter pruning down to 3-4 feet ensures huge crop of sweet berries."),

            ("Red Lady Papaya", "پپیتا (ریڈ لیڈی 786)", "Red Lady Papaya", "Carica papaya 'Red Lady'", "FRUIT",
             "Dwarf high-yielding sweet hybrid papaya tree producing aromatic salmon-red fruit in under 9 months.",
             "بونا ہائبرڈ پپیتا جو صرف نو ماہ میں میٹھے، خوشبودار اور سرخ گودے والے پپیتے دیتا ہے۔ گھریلو باغات کے لیے لاجواب ہے۔",
             2, 20, "None", "Full Sun", False, "Requires excellent drainage; roots rot quickly in standing water during monsoon rains."),

            ("Jamun / Black Plum", "دیسی جامن", "Jamun", "Syzygium cumini", "FRUIT",
             "Majestic indigenous shade tree yielding dark purple juicy berries renowned for blood sugar control.",
             "پاکستان کا روایتی درخت جو برسات میں رسیلے کالے جامن دیتا ہے۔ اس کی گٹھلیوں کا سفوف شوگر کے مریضوں کے لیے قدرتی اکسیر ہے۔",
             4, 60, "Post-harvest", "Full Sun", False, "Deep-rooted and wind-resistant; flourishes across Punjab, Sindh, and KPK."),

            ("Sufi Ber / Desi Jujube", "دیسی صوفی بیر", "Sufi Ber", "Ziziphus mauritiana", "FRUIT",
             "Extremely tough desert fruit tree producing crisp, sweet-tangy apple-shaped winter berries.",
             "شدید خشک سالی برداشت کرنے والا دیسی درخت جو سردیوں میں خستہ اور میٹھے گول بیر دیتا ہے۔ پرندوں کی پسندیدہ پناہ گاہ۔",
             5, 60, "Severe May Pruning", "Full Sun", False, "Prune heavily in May after harvest to stimulate lush new fruiting branches."),

            ("Pothohar Olive / Zaitoon", "زیتون کا پودا (پوٹھوہار)", "Zaitoon", "Olea europaea", "FRUIT",
             "Evergreen silvery-foliaged blessed tree flourishing in the Pothohar and Chakwal olive valleys.",
             "قرآنی برکتوں والا سدا بہار درخت جو پنجاب کے پوٹھوہار ریجن اور خیبر پختونخوا میں شاندار پھل اور خالص تیل دیتا ہے۔",
             5, 90, "Winter", "Full Sun", False, "Thrives on stony, alkaline slopes; highly drought and heat tolerant once established."),

            # Indigenous Trees & Shade
            ("Neem", "نیم", "Neem", "Azadirachta indica", "TREE",
             "Miraculous medicinal tree purifying air, cooling courtyards, and providing organic pesticide.",
             "طبی خصوصیات کا حامل سدا بہار درخت جو ہوا کو صاف کرتا ہے اور شدید گرمی میں ٹھنڈی چھاؤں دیتا ہے۔ اس کے پتوں سے کیڑے مار دوا بنتی ہے۔",
             5, 90, "Monsoon", "Full Sun", False, "Natural antibiotic and pesticide for the entire garden ecosystem."),

            ("Moringa / Sohanjna", "سوہانجنا (مورنگا)", "Sohanjna", "Moringa oleifera", "TREE",
             "Miracle superfood tree whose drumsticks and leaves cure nutritional deficiencies.",
             "معجزاتی درخت جس کے پتے اور پھلیاں بے شمار بیماریوں کا شافی علاج ہیں۔ شوگر اور بلڈ پریشر میں مفید ہے۔",
             4, 60, "Post-harvest", "Full Sun", False, "Fastest growing tree in Pakistan; drought tolerant."),

            ("Sukh Chain / Pongamia", "سکھ چین", "Sukh Chain", "Pongamia pinnata", "TREE",
             "Dense-canopy shade tree with lilac flowers lining Pakistani avenues and lawns.",
             "گھنی چھاؤں اور ہلکے جامنی خوشبودار پھولوں والا سایہ دار درخت، شہروں کی آلودگی کو کم کرتا ہے۔",
             5, 90, "Winter", "Full Sun", False, "Excellent shade and nitrogen-fixing tree for domestic front lawns."),

            ("Sheesham / Tahli", "شیشم (ٹاہلی)", "Sheesham", "Dalbergia sissoo", "TREE",
             "Stately indigenous Punjab rosewood timber tree with fluttering green leaflets.",
             "پنجاب کا روایتی درخت جو بہترین فرنیچر کی لکڑی فراہم کرتا ہے اور دہائیوں تک قائم رہتا ہے۔",
             6, 120, "Winter", "Full Sun", False, "Indigenous to Punjab and Khyber Pakhtunkhwa."),

            ("Bakain / Chinaberry", "بکائن", "Bakain", "Melia azedarach", "TREE",
             "Fast-growing shade tree resembling Neem, covered in fragrant purple spring blossoms.",
             "نیم کی طرح نظر آنے والا تیزی سے بڑھنے والا درخت، بہار میں خوشبودار جامنی پھول لاتا ہے۔",
             5, 90, "Winter", "Full Sun", False, "Hardy and drought tolerant across plains of Pakistan.")
        ]

        plant_image_map = {
            "Ficus carica": "plants/injeer_fig_tree.jpg",
            "Grewia asiatica": "plants/falsa_berry_bush.jpg",
            "Chrysanthemum morifolium": "plants/chrysanthemum_morifolium_hd.jpg",
            "Dahlia pinnata": "plants/dahlia_pinnata_hd.jpg",
            "Gazania rigens": "plants/gazania_rigens_hd.jpg",
            "Pelargonium hortorum": "plants/pelargonium_geranium_hd.jpg",
            "Catharanthus roseus nanus": "plants/catharanthus_roseus_nanus.jpg",
            "Sansevieria trifasciata": "plants/snake_plant_sansevieria.jpg",
            "Chlorophytum comosum": "plants/spider_plant_chlorophytum.jpg",
            "Spathiphyllum wallisii": "plants/peace_lily_indoor_hd.jpg",
            "Dypsis lutescens": "plants/areca_palm_dypsis.jpg",
            "Ficus lyrata": "plants/fiddle_leaf_fig.jpg",
            "Epipremnum aureum 'Marble Queen'": "plants/marble_queen_pothos.jpg",
            "Crassula ovata": "plants/jade_plant_crassula.jpg",
            "Adenium obesum": "plants/adenium_desert_rose_hd.jpg",
            "Kalanchoe blossfeldiana": "plants/kalanchoe_blooming_hd.jpg",
            "Coleus amboinicus": "plants/ajwain_leaf_potted_hd.jpg",
            "Cymbopogon citratus": "plants/lemongrass_cymbopogon.jpg",
            "Trigonella foenum-graecum": "plants/kasuri_methi_trigonella.jpg",
            "Foeniculum vulgare": "plants/saunf_sweet_fennel_hd.jpg",
            "Spinacia oleracea 'Desi'": "plants/desi_palak_spinach_hd.jpg",
            "Manilkara zapota 'Sindh Golden'": "plants/sindh_golden_chikoo.jpg",
            "Carica papaya 'Red Lady'": "plants/red_lady_papaya_786.jpg",
            "Syzygium cumini": "plants/desi_jamun_black_plum.jpg",
            "Ziziphus mauritiana": "plants/sufi_ber_jujube_hd.jpg",
            "Olea europaea": "plants/pothohar_olive_zaitoon.jpg",
        }

        created_plants = []
        plant_lookup = {}
        for p in plants_data:
            obj, _ = Plant.objects.get_or_create(
                scientific_name=p[3],
                defaults={
                    'name_en': p[0],
                    'name_ur': p[1],
                    'name_roman': p[2],
                    'category': p[4],
                    'description_en': p[5],
                    'description_ur': p[6],
                    'watering_interval_days': p[7],
                    'fertilizer_interval_days': p[8],
                    'pruning_season': p[9],
                    'sunlight_requirement': p[10],
                    'is_indoor_suitable': p[11],
                    'climate_notes_pakistan': p[12],
                }
            )
            if p[3] in plant_image_map:
                obj.image = plant_image_map[p[3]]
                obj.save(update_fields=['image'])
            created_plants.append(obj)
            plant_lookup[obj.scientific_name] = obj
            if obj.name_roman:
                plant_lookup[obj.name_roman.lower()] = obj

        self.stdout.write(f"  -> Successfully seeded {len(created_plants)} botanical plant profiles.")

        # 3. Diseases, Agronomic Medicines & Dual Treatments
        self.stdout.write("Seeding plant diseases, agricultural medicines, and treatment protocols...")
        diseases_data = [
            ("Safaid Makhi (Whitefly)", "سفید مکھی کا حملہ", "Safaid Makhi", "Bemisia tabaci", "HIGH",
             "Tiny white flies under leaves, yellowing of leaves, sooty black mold formation, sticky honeydew.",
             "پتوں کے نیچے سفید رنگ کی باریک مکھیاں اڑتی ہوئی نظر آتی ہیں۔ پتے پیلے پڑ جاتے ہیں اور ان پر کالی پھپھوندی جم جاتی ہے۔",
             "Spray 5ml organic cold-pressed Neem oil mixed with 2ml liquid soap in 1L water every 4 days. Hang yellow sticky cards.",
             "ایک لیٹر پانی میں 5 ملی لیٹر نیم کا تیل اور چند قطرے برتن دھونے والا صابن ملا کر شام کے وقت پتوں کے نیچے اسپرے کریں۔ پیلے چپکنے والے کارڈز لگائیں۔",
             "Apply Imidacloprid (Confidor 200 SL) at 1ml per liter or Movento at 1ml per liter during severe infestation.",
             "ایمیڈاکلوپرڈ (کانفیڈور) 1 ملی لیٹر فی لیٹر یا مووینٹو 1 ملی لیٹر فی لیٹر کے حساب سے پتوں کے نیچے اسپرے کریں۔",
             "کیمیائی اسپرے کرتے وقت ماسک اور دستانے پہنیں۔ پھل اور سبزی اسپرے کے 7 دن بعد تک استعمال نہ کریں۔",
             ["Solanum lycopersicum", "Capsicum annuum", "Solanum melongena", "Abelmoschus esculentus", "Rosa damascena", "Citrus limon", "Carica papaya 'Red Lady'"]),

            ("Powdery Mildew / Safaid Phaphondi", "سفید پھپھوندی (پاؤڈری ملڈیو)", "Safaid Phaphondi", "Erysiphe cichoracearum", "MEDIUM",
             "White talcum powder-like spots appearing on upper leaf surfaces and buds, causing leaf curling and drying.",
             "پتوں کی اوپری سطح پر سفید ٹیلکم پاؤڈر جیسے دھبے نمودار ہوتے ہیں جس سے پتے مڑ کر خشک ہونے لگتے ہیں۔",
             "Mix 1 part fresh cow milk with 9 parts water and spray in morning sun. Dust fine wood ash over wet foliage.",
             "ایک حصہ گائے کا دودھ 9 حصے پانی میں ملا کر صبح کی دھوپ میں اسپرے کریں۔ دیسی لکڑی کی باریک راکھ چھڑکیں۔",
             "Apply Wettable Sulphur 80% WP at 2g/L or Score 250 EC (Difenoconazole) at 0.5ml per liter.",
             "کیمیائی علاج میں سلفر پاؤڈر 2 گرام فی لیٹر یا اسکور فنگسائیڈ آدھا ملی لیٹر فی لیٹر اسپرے کریں۔",
             "تیز دھوپ اور دوپہر کے وقت سلفر اسپرے نہ کریں ورنہ پتے جل سکتے ہیں۔",
             ["Rosa damascena", "Cucumis sativus", "Luffa acutangula", "Momordica charantia", "Tagetes erecta", "Chrysanthemum morifolium", "Mentha spicata"]),

            ("Leaf Curl Virus / Marorha Rog", "پتہ مروڑ وائرس (مروڑھا روگ)", "Patta Marorha", "Chilli leaf curl virus", "CRITICAL",
             "Leaves curling upwards like a boat, stunted plant growth, thickening of veins, brittle foliage.",
             "پتے کشتی نما اوپر کی طرف مڑ جاتے ہیں، پودے کا قد چھوٹا رہ جاتا ہے اور نئی کونپلیں بننا رک جاتی ہیں۔",
             "Eliminate whitefly vectors using yellow glue sheets and neem garlic tea. Rogue out and safely burn heavily stunted plants.",
             "یہ وائرس سفید مکھی سے پھیلتا ہے۔ پیلے چپکنے والے کارڈز لگائیں اور بیمار پودوں کو اکھاڑ کر دور دبا دیں تاکہ دوسرے پودے محفوظ رہیں۔",
             "Apply systemic insecticide Movento (Spirotetramat) at 1ml/L or Match 50 EC at 1ml/L to control transmitting vector insects.",
             "وائرس پھیلانے والے کیڑوں کے خاتمے کے لیے مووینٹو 1 ملی لیٹر یا میچ 1 ملی لیٹر فی لیٹر پانی میں اسپرے کریں۔",
             "وائرس کا کوئی براہ راست کیمیائی علاج نہیں ہے؛ صرف سفید مکھی کو مار کر اس کا پھیلاؤ روکا جا سکتا ہے۔",
             ["Capsicum annuum", "Solanum lycopersicum", "Carica papaya 'Red Lady'", "Abelmoschus esculentus", "Capsicum annuum grossum"]),

            ("Susti Kida / Aphids", "سست کیڑا (تیلا)", "Sust Kida / Tela", "Aphis gossypii", "MEDIUM",
             "Clusters of tiny green/black insects sucking sap on tender new shoots and buds.",
             "نرم کونپلوں اور کلیوں پر سبز اور سیاہ رنگ کے ننھے کیڑوں کا جمگھٹا جو پودے کا رس چوستے ہیں۔",
             "Blast with strong water jet from garden hose. Spray garlic-chilli tea or mild soapy water (3ml/L).",
             "تیز پانی کی دھار سے کیڑوں کو دھو دیں۔ لہسن اور ہری مرچ کو پانی میں پکا کر چھان لیں اور پودے پر اسپرے کریں۔",
             "Apply Acetamiprid 20% SP at 1g per liter or Confidor at 0.5ml per liter for immediate knock-down.",
             "ایسیٹامیپرڈ 1 گرام فی لیٹر یا کانفیڈور آدھا ملی لیٹر فی لیٹر پانی میں ملا کر اسپرے کریں۔",
             "شام کے وقت اسپرے کریں تاکہ مفید کیڑے (لیڈی برڈ بیٹل) محفوظ رہیں۔",
             ["Rosa damascena", "Coriandrum sativum", "Spinacia oleracea", "Citrus limon", "Chrysanthemum morifolium", "Trigonella foenum-graecum"]),

            ("Jad Ki Saran / Root Rot", "جڑوں کی سڑن (روٹ راٹ)", "Jad ki Saran", "Fusarium / Pythium", "HIGH",
             "Wilting of whole plant despite moist soil, blackened mushy decaying roots, foul damp odor.",
             "مٹی میں نمی کے باوجود پودا مرجھا جاتا ہے، گملے سے پودا نکالنے پر جڑیں سیاہ، نرم اور بدبودار نکلتی ہیں۔",
             "Immediately stop watering. Repot into fresh well-draining bhal soil mixed with river sand. Dust roots with cinnamon powder.",
             "فوری طور پر پانی دینا بند کریں۔ پودے کو گملے سے نکال کر سڑی ہوئی جڑیں کاٹیں اور تازہ بھل و ریتلی مٹی میں لگائیں۔ دار چینی پاؤڈر چھڑکیں۔",
             "Drench root zone thoroughly with Carbendazim 50% WP (Derosal) at 2g/L or Topsin-M at 1.5g/L.",
             "کاربینڈازم (ڈیروسال) 2 گرام فی لیٹر یا ٹاپسن ایم 1.5 گرام فی لیٹر کا محلول تیار کر کے جڑوں میں ڈالیں۔",
             "گملے کے پیندے میں نکاسی کا سوراخ ہمیشہ کھلا رکھیں۔ ضرورت سے زیادہ پانی پودے کا سب سے بڑا دشمن ہے۔",
             ["Epipremnum aureum", "Sansevieria trifasciata", "Aloe barbadensis miller", "Adenium obesum", "Solanum lycopersicum", "Spathiphyllum wallisii"]),

            ("Downy Mildew / Zard Chitki", "ڈاؤنی ملڈیو (زرد چٹکی پھپھوندی)", "Downy Mildew", "Pseudoperonospora cubensis", "HIGH",
             "Angular yellow-green oily patches on leaf tops with purple-grey downy felt on undersides in cucurbits.",
             "پتوں کی اوپری سطح پر کونے دار پیلے دھبے اور نچلی سطح پر جامنی سرمئی روئی جیسی پھپھوندی۔ کدو، کھیرے اور توری کے پتے تیزی سے سوکھ جاتے ہیں۔",
             "Spray solution of 5g baking soda (sodium bicarbonate) and 5ml cold-pressed neem oil in 1L warm water every 5 days.",
             "ایک لیٹر پانی میں 5 گرام میٹھا سوڈا (بیکنگ سوڈا) اور 5 ملی لیٹر نیم آئل ملا کر پتوں کے نچلے حصے پر اسپرے کریں۔ پودوں کے درمیان ہوا کا گزر بحال رکھیں۔",
             "Apply Ridomil Gold MZ (Mefenoxam + Mancozeb) at 2.5g per liter or Aliette (Fosetyl-Al) at 2g per liter.",
             "ریڈومل گولڈ (Ridomil Gold) 2.5 گرام فی لیٹر یا ایلیٹ (Aliette) 2 گرام فی لیٹر پانی میں گھول کر 10 دن کے وقفے سے اسپرے کریں۔",
             "حفاظتی چشمہ اور دستانے پہنیں۔ اسپرے کے بعد 5 دن تک پھل نہ توڑیں۔",
             ["Cucumis sativus", "Luffa acutangula", "Momordica charantia", "Spinacia oleracea", "Mentha spicata"]),

            ("Early Blight / Agiti Jhalso", "اگیتی جھلساؤ (آلٹرنیریا داغ)", "Early Blight", "Alternaria solani", "HIGH",
             "Dark brown to black concentric target rings surrounded by yellow halos on older lower leaves.",
             "ٹماٹر اور آلو کے پرانے نچلے پتوں پر سیاہ گول نشانے (ٹارگٹ بورڈ نما چھلے) اور پیلا بارڈر۔ پتے سوکھ کر جلنے لگتے ہیں۔",
             "Prune away all lower infected leaves touching the soil. Mulch heavily with dry straw. Spray aerated compost tea weekly.",
             "مٹی کے ساتھ لگے ہوئے تمام بیمار پتے کینچی سے کاٹ کر تلف کریں۔ مٹی پر صاف خشک گھاس کی ملچنگ کریں تاکہ پانی کے چھینٹوں سے بیماری نہ پھیلے۔",
             "Spray Nativo (Tebuconazole + Trifloxystrobin) at 0.65g/L or Score 250 EC (Difenoconazole) at 0.5ml/L every 10-12 days.",
             "نیٹیوو (Nativo) فنگسائیڈ 0.65 گرام فی لیٹر یا اسکور (Score) آدھا ملی لیٹر فی لیٹر کے حساب سے بیماری دیکھتے ہی اسپرے کریں۔",
             "سبزی توڑنے کے بعد اسپرے کریں تاکہ کیمیکل کا اثر کھانے میں نہ آئے۔",
             ["Solanum lycopersicum", "Solanum melongena", "Capsicum annuum grossum"]),

            ("Late Blight / Pachiti Jhalso", "پچھیتی جھلساؤ (فائیٹوف تھورا وباء)", "Late Blight", "Phytophthora infestans", "CRITICAL",
             "Rapidly spreading water-soaked dark brown greasy lesions on leaves, stems, and fruits with white fungal mold under cool humid conditions.",
             "ٹھنڈے اور نمی والے موسم میں پتوں، تنے اور ٹماٹروں پر پانی بھرے سیاہ چکنے داغ جو چند دنوں میں پورے پودے کو جلا کر راکھ کر دیتے ہیں۔",
             "Immediately destroy and bury heavily infected plants. Keep foliage completely dry, improve air circulation, and apply copper soap spray.",
             "شدید بیمار پودوں کو فوراً جڑوں سمیت اکھاڑ کر زمین میں دبا دیں۔ پتوں پر اوپر سے پانی نہ ڈالیں اور پودوں کو کھلی دھوپ اور ہوا دار جگہ پر رکھیں۔",
             "Spray Acrobat (Dimethomorph) at 2g/L tank-mixed with Mancozeb (2.5g/L), or Curzate (Cymoxanil + Mancozeb) at 2.5g/L.",
             "ایکرو بیٹ (Acrobat) 2 گرام فی لیٹر یا کرزیٹ (Curzate) 2.5 گرام فی لیٹر پانی میں ملا کر ہر 7 دن بعد اسپرے کریں۔",
             "شدید متعدی بیماری ہے؛ کام کرنے کے بعد باغبانی کے تمام اوزار ڈیٹول یا الکوحل سے صاف کریں۔",
             ["Solanum lycopersicum", "Solanum melongena"]),

            ("Spider Mites / Laal Makri", "لال مکڑی (مکڑی جالا روگ)", "Spider Mites / Laal Makri", "Tetranychus urticae", "HIGH",
             "Fine delicate silky webbing across leaf undersides, bronzed dusty foliage, tiny yellow speckling, and leaf drop during hot dry spells.",
             "گرم اور خشک موسم میں پتوں کے نیچے باریک جالا، زرد اور کانسی رنگ کے دھبے اور مائیکروسکوپک ننھی سرخ مکھیاں جو پودے کا رس نچوڑ لیتی ہیں۔",
             "Blast leaf undersides with high-pressure cold water hose. Spray rosemary oil or pure neem oil (5ml/L) with liquid soap twice weekly.",
             "پتوں کے نیچے تیز ٹھنڈے پانی کی دھار مار کر جالے توڑیں۔ 5 ملی لیٹر نیم آئل میں چند قطرے مائع صابن ملا کر ہفتے میں دو بار اسپرے کریں۔",
             "Apply Oberon 240 SC (Spiromesifen) at 1ml/L or Agrimec / Vertimec (Abamectin) at 0.5ml/L targeting leaf undersides thoroughly.",
             "اوبیرون (Oberon) 1 ملی لیٹر فی لیٹر یا ورٹیمیک (Abamectin) آدھا ملی لیٹر فی لیٹر شام کے وقت پتوں کے نیچے اچھی طرح اسپرے کریں۔",
             "شدید گرمی کی دوپہر میں اسپرے نہ کریں ورنہ پتے جل سکتے ہیں۔",
             ["Rosa damascena", "Tagetes erecta", "Solanum lycopersicum", "Solanum melongena", "Citrus limon", "Adenium obesum", "Dahlia pinnata"]),

            ("Mealybugs / Chipi Kida", "ملی بگ (چپی سفید کیڑا)", "Mealybugs / Chipi Kida", "Planococcus citri", "HIGH",
             "Clusters of soft-bodied insects covered in white powdery cottony wax hiding in leaf axils, sucking sap and causing sticky black mold.",
             "پودوں کی شاخوں اور پتوں کے جوڑوں میں سفید روئی جیسے چپکے ہوئے کیڑوں کے جھنڈ جو رس چوس کر پودے کو کمزور اور کالا کر دیتے ہیں۔",
             "Dip cotton swab in 70% isopropyl alcohol and dab directly on mealybug clusters. Spray potassium soap or neem oil emulsified with garlic water.",
             "روئی کی تیلی کو اسپرٹ (الکوحل) میں بھگو کر کیڑوں پر لگائیں تاکہ ان کا مومی غلاف پگھل جائے۔ پھر لہسن اور نیم کے پانی کا تیز اسپرے کریں۔",
             "Apply Movento 240 SC (Spirotetramat) at 1ml/L as two-way systemic insecticide, or Confidor (Imidacloprid) root zone drench.",
             "مووینٹو (Movento) 1 ملی لیٹر فی لیٹر پانی میں ملا کر اسپرے کریں یا کانفیڈور کی جڑوں میں ڈرینچنگ کریں۔",
             "گھریلو استعمال کے پودوں پر کیمیکل اسپرے کے بعد کم از کم 10 دن تک احتیاط برتیں۔",
             ["Citrus limon", "Psidium guajava", "Mangifera indica", "Epipremnum aureum", "Rosa damascena", "Ficus lyrata", "Dypsis lutescens"]),

            ("Citrus Canker / Nimbu ka Kankur", "لیموں کا کینکر (کھرنڈ روگ)", "Citrus Canker", "Xanthomonas axonopodis pv. citri", "CRITICAL",
             "Raised rough corky brown crater-like scabs surrounded by distinct oily yellow halos on leaves, twigs, and lemon citrus fruit rinds.",
             "لیموں اور مالٹے کے پتوں، شاخوں اور پھل پر ابھرے ہوئے کھردرے بھورے چھالے اور پیلے ہالے جو پھل کی خوبصورتی اور رس ضائع کر دیتے ہیں۔",
             "Prune out diseased twigs during dry winter weather and burn them. Spray freshly prepared Bordeaux mixture (1:1 copper sulfate and lime).",
             "موسم سرما کے خشک دنوں میں بیمار شاخیں کاٹ کر جلا دیں۔ تانبے کے سلفیٹ (نیلا تھوتھا) اور بجھے ہوئے چونے کا دیسی بورڈو مکسچر اسپرے کریں۔",
             "Apply Copper Oxychloride 50% WP (Cuprocaffaro) at 3g/L combined with Streptomycin sulfate antibiotic at 0.5g/L during spring flush.",
             "کاپر آکسی کلورائیڈ 3 گرام فی لیٹر اور اسٹریپٹو مائیسین اینٹی بائیوٹک 0.5 گرام فی لیٹر نئی پھوٹ کے وقت اسپرے کریں۔",
             "کٹائی کے اوزاروں کو ہر پودے کے بعد الکوحل سے جراثیم کش کریں۔",
             ["Citrus limon", "Psidium guajava"]),

            ("Anthracnose / Kaali Saran", "اینتھراکنوز (کالی سڑن و جھلسن)", "Anthracnose", "Colletotrichum gloeosporioides", "HIGH",
             "Sunken circular dark brown to pitch-black necrotic lesions on leaves, stems, and ripening fruits, oozing pinkish-salmon spore droplets.",
             "پتوں، شاخوں اور آم و پپیتے کے پھلوں پر گہرے کالے گڑھے نما داغ جن میں برسات کے دوران گلابی رطوبت نکلتی ہے۔ شاخیں اوپر سے نیچے سوکھتی ہیں۔",
             "Prune infected twigs 4 inches below the infected zone. Spray composted cow urine bio-extract or fermented garlic-chilli tea.",
             "بیمار شاخ کے متاثرہ حصے سے چار انچ نیچے سے کٹائی کریں۔ لہسن، ہری مرچ اور نیم کے پتوں کا قہوہ پکا کر ٹھنڈا کر کے اسپرے کریں۔",
             "Apply Topsin-M 70% WP (Thiophanate-Methyl) at 1.5g/L or Antracol (Propineb) at 2.5g/L before and after monsoon rains.",
             "ٹاپسن ایم (Topsin-M) 1.5 گرام فی لیٹر یا اینٹراکول 2.5 گرام فی لیٹر برسات سے پہلے اور بعد میں اسپرے کریں۔",
             "پھلوں کی چنائی کے وقت پھل پر داغ نہ لگنے دیں۔",
             ["Mangifera indica", "Carica papaya 'Red Lady'", "Psidium guajava", "Rosa damascena", "Ficus carica"]),

            ("Damping Off / Poudon ka Girna", "پنیری کا گرنا (ڈیمپنگ آف کالر راٹ)", "Damping Off", "Rhizoctonia solani / Pythium", "CRITICAL",
             "Newly germinated seedlings develop water-soaked constriction at soil level, topple over, and rot away en masse within 24 hours.",
             "نئے اگنے والے ننھے پودے زمین کی سطح سے نرم پڑ کر اچانک زمین پر گر جاتے ہیں اور چند ہی گھنٹوں میں پوری پنیری گل سڑ جاتی ہے۔",
             "Dust soil trays with ground Ceylon cinnamon powder (natural antifungal). Use well-draining sterile river sand and avoid overwatering seeds.",
             "مٹی کے اوپر دار چینی کا باریک پاؤڈر چھڑکیں جو قدرتی اینٹی فنگل ہے۔ بیجوں کو زیادہ گہرا نہ دبائیں اور صرف اسپرے بوتل سے نمی دیں۔",
             "Drench nursery seedling beds with Previcur Energy (Propamocarb + Fosetyl) at 1.5ml/L or treat seeds with Thiram 75% WP before sowing.",
             "پریویکور انرجی (Previcur Energy) 1.5 ملی لیٹر فی لیٹر پانی میں ملا کر پنیری کی جڑوں میں ڈالیں یا بیج بونے سے قبل فنگسائیڈ پاؤڈر لگائیں۔",
             "پنیری کے برتنوں میں نکاسی کے سوراخ کھلے رکھیں۔",
             ["Solanum lycopersicum", "Capsicum annuum", "Spinacia oleracea", "Coriandrum sativum", "Tagetes erecta", "Petunia hybrida"]),

            ("Leaf Miner / Patta Kuredne Wala Kida", "پتہ سرنگ کیڑا (لیف مائنر)", "Leaf Miner", "Liriomyza sativae", "MEDIUM",
             "Silvery translucent winding serpentine tunnels etched inside leaf layers, leading to leaf distortion, drying, and reduced photosynthesis.",
             "پتوں کے اندر سانپ نما چمکدار سفید لکیریں اور سرنگیں جن کے اندر باریک کیڑا پتے کا سبز مادہ کھاتا ہے، جس سے پتا مڑ کر سوکھ جاتا ہے۔",
             "Hang yellow sticky glue sheets near foliage to catch adult flies. Spray 5% neem seed kernel extract (NSKE) directly onto mined foliage.",
             "پودوں کے پاس پیلے چپکنے والے کارڈز لٹکائیں تاکہ اڑنے والی مکھیاں پھنس جائیں۔ نیم کے بیجوں کے مغز کا 5 فیصد عرق اسپرے کریں۔",
             "Spray Match 50 EC (Lufenuron) at 1ml/L or Tracer / Spinosad at 0.5ml/L penetrating deep into leaf epidermal layers.",
             "میچ (Match) 1 ملی لیٹر فی لیٹر یا ٹریسر (Spinosad) آدھا ملی لیٹر فی لیٹر اسپرے کریں جو پتے کے اندر داخل ہو کر سرنگ کیڑے کو مارتی ہے۔",
             "شام کے بعد اسپرے کریں اور پھولوں پر اسپرے سے گریز کریں۔",
             ["Solanum lycopersicum", "Citrus limon", "Cucumis sativus", "Spinacia oleracea", "Pelargonium hortorum"]),

            ("Blossom End Rot / Penda Sarna", "ٹماٹر کا پیندہ سڑنا (کیلشیم کمی)", "Blossom End Rot", "Physiological Calcium Deficiency", "MEDIUM",
             "Water-soaked dark leathery sunken black rot appearing at the blossom end (bottom) of tomatoes, bell peppers, and eggplants.",
             "ٹماٹر اور شملہ مرچ کے پیندے (نچلے حصے) پر سیاہ، چمڑے نما چپٹا گڑھا جو کیلشیم کی کمی اور بے قاعدہ پانی دینے کی وجہ سے ہوتا ہے۔",
             "Steep crushed eggshells in white vinegar for 48 hours, dilute 1:10 with water and drench roots. Maintain steady uniform soil moisture with drip.",
             "انڈوں کے باریک چھلکے سرکے میں دو دن بھگو کر پانی میں ملا کر جڑوں میں ڈالیں۔ پودے کو خشک ہونے سے بچائیں اور مستقل نمی رکھیں۔",
             "Apply foliar spray of Calcium Nitrate (CaNO3) at 2g per liter during active flowering and fruit set, plus agricultural gypsum in soil.",
             "کیلشیم نائٹریٹ 2 گرام فی لیٹر پانی میں حل کر کے پھول اور پھل بننے کے دوران پتوں پر اسپرے کریں اور گملے میں جپسم کا چمچ ملائیں۔",
             "بہت زیادہ نائٹروجن کھاد دینے سے گریز کریں کیونکہ یہ کیلشیم کے جذب ہونے کو روکتی ہے۔",
             ["Solanum lycopersicum", "Capsicum annuum grossum", "Solanum melongena", "Capsicum annuum"]),

            ("Iron Chlorosis / Pila Pan", "پتوں کا پیلا پن (آئرن و مائیکرو نیوٹرینٹ کمی)", "Iron Chlorosis", "Micronutrient Deficiency", "LOW",
             "New top leaves turn pale yellow to ivory while veins stay conspicuously dark green, caused by high pH alkaline soils locking up iron.",
             "نئی کونپلیں اور پتے زرد یا سفید ہو جاتے ہیں لیکن پتوں کی رگیں گہری سبز رہتی ہیں۔ یہ پاکستانی الکلائن مٹی میں فولاد کی کمی کی علامت ہے۔",
             "Drench soil with fermented citrus peel bio-enzyme mixed with diluted sour curd (chaach). Add well-rotted leaf mold compost.",
             "لیموں اور مالٹے کے چھلکوں سے تیار کردہ بائیو اینزائم یا کھٹی لسی پانی میں ملا کر جڑوں میں ڈالیں تاکہ مٹی کی تیزابیت متوازن ہو۔",
             "Dissolve Chelated Iron EDDHA 6% (Fe-EDDHA) at 5g in 10 liters of water and drench into root zone, or spray zinc-iron chelate foliar mix.",
             "چلیٹڈ آئرن (Fe-EDDHA 6%) 5 گرام فی 10 لیٹر پانی میں گھول کر جڑوں میں دیں، پتے 48 گھنٹوں میں دوبارہ گہرے سبز ہو جائیں گے۔",
             "دوپہر کی سخت دھوپ میں نہ ڈالیں، شام کو نم مٹی میں اپلائی کریں۔",
             ["Citrus limon", "Psidium guajava", "Rosa damascena", "Jasminum sambac", "Bougainvillea spectabilis"])
        ]

        disease_image_map = {
            "Pseudoperonospora cubensis": "diseases/disease_downy_mildew.jpg",
            "Alternaria solani": "diseases/disease_early_blight_tomato.jpg",
            "Phytophthora infestans": "diseases/disease_late_blight_potato.jpg",
            "Tetranychus urticae": "diseases/disease_spider_mites_red.jpg",
            "Planococcus citri": "diseases/disease_mealybugs_cottony.jpg",
            "Xanthomonas axonopodis pv. citri": "diseases/disease_citrus_canker_scab.jpg",
            "Colletotrichum gloeosporioides": "diseases/disease_anthracnose_rot.jpg",
            "Rhizoctonia solani / Pythium": "diseases/disease_damping_off_seedlings.jpg",
            "Liriomyza sativae": "diseases/disease_leaf_miner_tunnels.jpg",
            "Physiological Calcium Deficiency": "diseases/disease_blossom_end_rot.jpg",
            "Micronutrient Deficiency": "diseases/disease_iron_chlorosis_yellowing.jpg",
        }

        for d in diseases_data:
            disease_obj, _ = Disease.objects.get_or_create(
                scientific_name=d[3],
                defaults={
                    'name_en': d[0],
                    'name_ur': d[1],
                    'name_roman': d[2],
                    'severity_level': d[4],
                    'symptoms_en': d[5],
                    'symptoms_ur': d[6],
                }
            )
            if not disease_obj.sample_image and d[3] in disease_image_map:
                disease_obj.sample_image = disease_image_map[d[3]]
                disease_obj.save(update_fields=['sample_image'])

            # Link to specific plant species
            susceptible_species = d[10] if len(d) > 10 else []
            for spec in susceptible_species:
                if spec in plant_lookup:
                    disease_obj.plants.add(plant_lookup[spec])
            if not susceptible_species:
                disease_obj.plants.add(*created_plants[:8])

            # Organic Treatment
            Treatment.objects.get_or_create(
                disease=disease_obj,
                treatment_type='ORGANIC',
                defaults={
                    'title_en': f"Organic Home Remedy for {disease_obj.name_en}",
                    'title_ur': f"{disease_obj.name_ur} کا دیسی و نامیاتی علاج",
                    'instructions_en': d[7],
                    'instructions_ur': d[8],
                    'safety_disclaimer_ur': "دیسی نسخے عام طور پر پودوں اور پالتو جانوروں کے لیے محفوظ ہیں۔",
                }
            )

            # Chemical Treatment
            Treatment.objects.get_or_create(
                disease=disease_obj,
                treatment_type='CHEMICAL',
                defaults={
                    'title_en': f"Agricultural Fungicide / Pesticide for {disease_obj.name_en}",
                    'title_ur': f"{disease_obj.name_ur} کے لیے زرعی کیمیائی دوا",
                    'instructions_en': d[9] if len(d) > 9 else d[7],
                    'instructions_ur': d[10] if len(d) > 11 else (d[8] if len(d) <= 10 else d[10]),
                    'safety_disclaimer_ur': d[11] if len(d) > 11 else d[9],
                }
            )

        self.stdout.write(f"  -> Successfully seeded {len(diseases_data)} diseases with dual organic/chemical treatments.")

        # 4. User Garden & Plants
        self.stdout.write("Seeding sample gardens, user plants, and tasks...")
        garden, _ = Garden.objects.get_or_create(
            owner=homeowner,
            name="احمد کا چھت کا نخلستان (Rooftop Oasis)",
            defaults={
                'location_address': 'مکان نمبر 45، بی بلاک، ماڈل ٹاؤن، لاہور',
                'city': 'Lahore',
                'total_budget': Decimal('50000.00'),
            }
        )

        GardenMember.objects.get_or_create(
            garden=garden,
            user=gardener,
            defaults={'role': 'GARDENER'}
        )

        GardenMember.objects.get_or_create(
            garden=garden,
            user=supervisor,
            defaults={'role': 'SUPERVISOR'}
        )

        # Seed UserPlants for Homeowner
        rose_template = Plant.objects.filter(name_roman__icontains='Gulab').first()
        lemon_template = Plant.objects.filter(name_roman__icontains='Nimbu').first()

        up1, _ = UserPlant.objects.get_or_create(
            user=homeowner,
            nickname="صحن کا سرخ گلاب",
            defaults={
                'plant_template': rose_template,
                'garden': garden,
                'location_description': 'مرکزی صحن - مٹی کا 18 انچ کا غملا',
                'is_indoor': False,
                'watering_interval_days': 2,
            }
        )
        CareCalendarService.generate_care_schedule(up1, days=14)

        up2, _ = UserPlant.objects.get_or_create(
            user=homeowner,
            nickname="چھت کا کاغذی لیموں",
            defaults={
                'plant_template': lemon_template,
                'garden': garden,
                'location_description': 'چھت کے کونے میں دھوپ والی جگہ',
                'is_indoor': False,
                'watering_interval_days': 3,
            }
        )
        CareCalendarService.generate_care_schedule(up2, days=14)

        # 5. Tasks in 5 States
        t1, _ = Task.objects.get_or_create(
            garden=garden,
            title="گلاب کی پرانی شاخوں کی کٹائی اور گملے کی گڈی",
            defaults={
                'description': 'دیسی گلاب کی سوکھی شاخیں کاٹیں اور مٹی میں 2 انچ گہری گڈی کر کے دیسی کھاد ملائیں۔',
                'state': 'APPROVED',
                'created_by': homeowner,
                'assigned_to': gardener,
                'due_date': date.today() - timedelta(days=2),
            }
        )
        TaskReport.objects.get_or_create(
            task=t1,
            defaults={
                'notes': 'گلاب کی کٹائی مکمل کر کے گڈی کر دی گئی ہے اور 5 کلو گلی سڑی گوبر کی کھاد ملا دی ہے۔',
                'supervisor_review_notes': 'کام تسلی بخش اور بہترین طریقے سے مکمل ہوا ہے۔ منظور شدہ۔',
                'reviewed_at': timezone.now(),
            }
        )

        t2, _ = Task.objects.get_or_create(
            garden=garden,
            title="لیموں کے پودے پر سفید مکھی کے خاتمے کے لیے نیم آئل اسپرے",
            defaults={
                'description': 'لیموں کے پتوں کے نیچے سفید مکھی دیکھی گئی ہے، شام کے وقت نیم کے تیل کا اسپرے کریں۔',
                'state': 'SUBMITTED',
                'created_by': supervisor,
                'assigned_to': gardener,
                'due_date': date.today(),
            }
        )
        TaskReport.objects.get_or_create(
            task=t2,
            defaults={
                'notes': 'شام 5 بجے پورے لیموں کے پودے اور ارد گرد کے گملوں پر نیم کے تیل کا باریک اسپرے کر دیا ہے۔',
            }
        )

        t3, _ = Task.objects.get_or_create(
            garden=garden,
            title="کچن گارڈن کے لیے پالک اور دھنیا کی نئی پنیری لگانا",
            defaults={
                'description': 'گرو بیگز میں نرم بھل مٹی بھر کر موسم سرما کی سبزیوں کی پنیری منتقل کریں۔',
                'state': 'IN_PROGRESS',
                'created_by': homeowner,
                'assigned_to': gardener,
                'due_date': date.today() + timedelta(days=2),
            }
        )

        t4, _ = Task.objects.get_or_create(
            garden=garden,
            title="ڈرپ اریگیشن پائپ اور نوزلز کی صفائی",
            defaults={
                'description': 'چھت پر لگے خودکار ڈرپ پائپوں کو چیک کریں اور بند نوزلز کھولیں۔',
                'state': 'ASSIGNED',
                'created_by': homeowner,
                'assigned_to': gardener,
                'due_date': date.today() + timedelta(days=4),
            }
        )

        t5, _ = Task.objects.get_or_create(
            garden=garden,
            title="موسم بہار کے پھولوں کے لیے نئے مٹی کے گملے خریدنا",
            defaults={
                'description': 'نرسری سے 12 انچ والے 10 عدد مٹی کے گملے لانا۔',
                'state': 'CREATED',
                'created_by': homeowner,
                'due_date': date.today() + timedelta(days=6),
            }
        )

        # Garden Expenses
        Expense.objects.get_or_create(
            garden=garden,
            title="دیسی گوبر کھاد اور بھل مٹی کی ٹرالی",
            defaults={
                'category': 'FERTILIZER',
                'amount': Decimal('4500.00'),
                'recorded_by': gardener,
                'expense_date': date.today() - timedelta(days=3),
            }
        )
        Expense.objects.get_or_create(
            garden=garden,
            title="مالی کی ماہانہ دیکھ بھال کی اجرت (نومبر)",
            defaults={
                'category': 'LABOR',
                'amount': Decimal('8000.00'),
                'recorded_by': homeowner,
                'expense_date': date.today() - timedelta(days=1),
            }
        )

        # 6. Marketplace Products (Expanded with 22 Agricultural Medicines, Fertilizers & Tools)
        self.stdout.write("Seeding verified nursery products & agricultural medicines in marketplace...")
        products = [
            # Medicines & Pest Controls
            ("خالص دیسی نیم کا تیل (Pure Organic Neem Oil 500ml)", 'PESTICIDE',
             "100% خالص ٹھنڈے طریقہ کار سے تیار شدہ نیم آئل۔ سفید مکھی، تیلا اور پاؤڈری ملڈیو کا قدرتی دشمن۔ پودوں کے لیے بے ضرر۔ (100% cold-pressed organic neem oil for natural pest control against whiteflies, aphids, mealybugs, and spider mites. Safe for vegetables and ornamental plants.)",
             Decimal('650.00'), 45),
            
            ("ریڈومل گولڈ پھپھوندی کش دوا (Ridomil Gold MZ 68 WG Fungicide 250g)", 'PESTICIDE',
             "ڈاؤنی ملڈیو اور پچھیتی جھلساؤ کے خاتمے کے لیے عالمی شہرت یافتہ سسٹمک فنگسائیڈ۔ سبزیوں اور بیلوں کا شافی علاج۔ (World-renowned systemic fungicide for complete control of downy mildew and late blight on vegetables, gourds, and vines.)",
             Decimal('1450.00'), 25),

            ("نیٹیوو جدید سسٹمک فنگسائیڈ (Nativo Broad Spectrum Fungicide 100g)", 'PESTICIDE',
             "ٹماٹر، مرچ اور پھولوں میں اگیتی جھلساؤ، پتوں کے داغ اور اینتھراکنوز کا جدید ترین اینٹی فنگل علاج۔ (Advanced dual-action systemic fungicide targeting early blight, leaf spots, and anthracnose on tomatoes, peppers, and roses.)",
             Decimal('1850.00'), 20),

            ("مووینٹو سسٹمک کیڑے مار دوا (Movento 240 SC Systemic Insecticide 100ml)", 'PESTICIDE',
             "دو طرفہ سسٹمک کیڑے مار دوا جو ملی بگ، سفید مکھی اور سست کیڑے کو چھپی ہوئی جگہوں سے ختم کرتی ہے۔ (Two-way systemic insecticide that penetrates plant vascular system to wipe out stubborn mealybugs, whiteflies, and aphids.)",
             Decimal('1650.00'), 18),

            ("کاپر آکسی کلورائیڈ کاپر فنگسائیڈ (Copper Oxychloride 50% WP 500g)", 'PESTICIDE',
             "لیموں کے کینکر، بیکٹیریل روگ اور کالی سڑن کے خلاف روایتی و آزمودہ کاپر اسپرے پاؤڈر۔ (Broad-spectrum contact copper fungicide and bactericide specifically recommended for citrus canker, leaf spots, and blights.)",
             Decimal('950.00'), 35),

            ("اوبیرون سرخ مکڑی مار دوا (Oberon Spider Mite & Whitefly Miticide 100ml)", 'PESTICIDE',
             "گلاب، سبزیوں اور سجاوٹی پودوں پر سرخ مکڑی کے جالوں اور انڈوں کا خاتمہ کرنے والی معیاری دوا۔ (Specialized miticide that eliminates adult spider mites, nymphs, and eggs on roses, vegetables, and container plants.)",
             Decimal('1750.00'), 15),

            ("پیلی چپکنے والی کیڑے مار شیٹس (Yellow Sticky Insect Traps Pack of 20)", 'PESTICIDE',
             "بغیر کسی کیمیکل کے سفید مکھی، لیف مائنر اور مچھروں کو پکڑنے والے ڈبل سائیڈڈ پیلے گلو کارڈز۔ (Non-toxic double-sided yellow glue traps for monitoring and mass trapping whiteflies, leafminers, fungus gnats, and aphids.)",
             Decimal('600.00'), 50),

            # Organic & Chemical Fertilizers
            ("نامیاتی گلی سڑی گوبر کھاد (Organic Aged Compost 10kg)", 'FERTILIZER',
             "دو سال پرانی تیار شدہ دیسی کھاد جو مٹی کی زرخیزی اور پھولوں کے سائز میں فوری اضافہ کرتی ہے۔ بالکل بو کے بغیر۔ (Two-year fully decomposed aged organic cow manure compost. Restores soil biology, enhances aeration, and enriches container soil naturally.)",
             Decimal('400.00'), 80),

            ("این پی کے متوازن کھاد (Balanced NPK 20-20-20 Fertilizer 1kg)", 'FERTILIZER',
             "پودوں کی مجموعی بڑھوتری، سبز پتوں اور بھرپور پھولوں کے لیے پانی میں حل پذیر معیاری کھاد۔ (Premium 100% water-soluble balanced NPK 20-20-20 macro-nutrient plant food with trace micronutrients for vibrant blooms and deep green leaves.)",
             Decimal('950.00'), 30),

            ("چلیٹڈ آئرن کھاد 6% (Chelated Iron EDDHA 6% Micronutrient 250g)", 'FERTILIZER',
             "پیلے پڑے پتوں کو 48 گھنٹوں میں گہرا سبز بنانے والی اعلیٰ ترین چلیٹڈ آئرن کھاد۔ الکلائن مٹی کے لیے اکسیر۔ (Premium EDDHA chelated iron specifically formulated for high pH alkaline Pakistani soils, curing leaf chlorosis and yellowing fast.)",
             Decimal('750.00'), 40),

            ("سرسوں کی قدرتی کھل کھاد (Pure Organic Mustard Cake Powder 2kg)", 'FERTILIZER',
             "روایتی سرسوں کی کھل جس کا مائع قہوہ پودوں کو نائٹروجن اور اینٹی فنگل مائیکروبیل طاقت دیتا ہے۔ (Traditional organic mustard oil cake meal rich in nitrogen, phosphorus, and natural compounds that ward off subterranean root pests.)",
             Decimal('380.00'), 65),

            ("اسٹیمڈ بون میل کھاد (Steamed Bone Meal Phosphorus Fertilizer 2kg)", 'FERTILIZER',
             "پھولوں اور پھلوں کی تعداد دگنی کرنے اور جڑوں کو مضبوط بنانے والی خالص نامیاتی فاسفورس کھاد۔ (Slow-release organic phosphorus and calcium source ideal for roses, fruit trees, and flowering annuals.)",
             Decimal('480.00'), 50),

            ("پریمیئم کوکو پیٹ بلاک (Premium Washed Coco Peat Block 5kg)", 'FERTILIZER',
             "نمی برقرار رکھنے اور جڑوں کو ہوا دار رکھنے والا 100% نامیاتی ناریل برادہ، 75 لیٹر مٹی تیار کرتا ہے۔ (Low-EC washed compressed coconut coir peat block expanding to 75 liters of rich water-retaining potting medium.)",
             Decimal('650.00'), 40),

            ("پرلائٹ و ورمی کیولائٹ سوائل مکس (Perlite & Vermiculite Aeration Mix 3L)", 'FERTILIZER',
             "گملے کی مٹی کو ہلکا، نرم اور ہوا دار بنانے والا قدرتی منرل مکسچر جو جڑوں کو سڑنے سے بچاتا ہے۔ (Lightweight sterile volcanic mineral mix that prevents soil compaction and maximizes drainage in pot culture.)",
             Decimal('550.00'), 30),

            # Live Plants & Seeds
            ("دیسی لال گلاب کا تیار پودا (Desi Red Rose in 12-inch Pot)", 'PLANTS',
             "خوشبودار دیسی سرخ گلاب کا تندرست اور کلیوں سے لدا پودا، مٹی کے پکے گملے میں تیار شدہ۔ (Fragrant native Desi Red Rose established in a 12-inch clay pot with fertile silt mix. Blooming with multiple healthy flower buds.)",
             Decimal('350.00'), 25),
             
            ("کاغذی لیموں کا پیوندی پودا (Grafted Kaghzi Lemon Plant)", 'PLANTS',
             "دو سالہ پیوندی لیموں کا پودا جو پہلے سال سے ہی وافر پھل دینا شروع کر دیتا ہے۔ (Two-year-old grafted Kaghzi Lemon sapling acclimated to Pakistani heat. High yield of thin-skinned, extra juicy fragrant lemons.)",
             Decimal('850.00'), 20),

            ("سانپ پودا / سنسویریا (Snake Plant in Ceramic Planter)", 'PLANTS',
             "ناسا کا منظور شدہ ایئر پیوریفائر پودا جو خوبصورت سیرامک گملے میں لگا ہوا ہے۔ انڈور کمروں کے لیے بہترین۔ (Hardy indoor Sansevieria snake plant in a modern glazed ceramic pot; releases oxygen 24/7.)",
             Decimal('1150.00'), 15),

            ("پریمیئم کچن گارڈن بیج پیکٹ 10 اقسام (Winter Kitchen Garden Seeds)", 'SEEDS',
             "ٹماٹر، ہری مرچ، پالک، دھنیا، مولی، گاجر، بینگن، سلاد پتہ، میتھی اور مٹر کے اعلیٰ جرمنیشن والے بیج۔ (Premium pack of 10 kitchen garden vegetable seeds with 85%+ germination rate.)",
             Decimal('750.00'), 60),

            # Planters & Pots
            ("روایتی مٹی کے پکے گملے (14-inch Terracotta Clay Pots)", 'POTS',
             "گجرات کے روایتی مٹی کے بنے ہوئے پکے گملے جن میں پودوں کی جڑیں ٹھنڈی رہتی ہیں اور ہوا کا گزر ہوتا ہے۔ (Traditional Gujrat handcrafted porous terracotta clay pot. Naturally cools root systems during intense summer heat.)",
             Decimal('280.00'), 50),

            # Tools & Smart Hardware
            ("باغبانی کٹر اور کانٹ چھانٹ قینچی (Heavy Duty Garden Pruning Shears)", 'TOOLS',
             "سٹین لیس سٹیل کا تیز دھار کٹر جو پودوں کی شاخوں کو بغیر نقصان پہنچائے صفائی سے کاٹتا ہے۔ (Heavy-duty ergonomic garden bypass pruning shears with rust-resistant carbon steel blades and safety thumb lock.)",
             Decimal('1200.00'), 15),

            ("5 لیٹر ہیوی ڈیوٹی پریشر اسپرے پمپ (5-Liter Garden Pressure Pump Sprayer)", 'TOOLS',
             "پیتل کی ایڈجسٹ ایبل نوزل اور پریشر ریلیف والو والی معیاری اسپرے بوتل جو کیڑے مار اور فنگسائیڈ اسپرے کے لیے بہترین ہے۔ (5-liter pressurized garden sprayer with adjustable brass nozzle and shoulder strap for even pesticide application.)",
             Decimal('2100.00'), 12),

            ("3-ان-1 ڈیجیٹل سوائل پی ایچ و نمی میٹر (3-in-1 Soil pH, Moisture & Sunlight Meter)", 'TOOLS',
             "بغیر بیٹری کے مٹی کی نمی، پی ایچ لیول اور دھوپ کی پیمائش کرنے والا سمارٹ ٹیسٹر میٹر۔ (Precision 3-in-1 probe measuring soil pH, moisture level, and ambient sunlight without batteries.)",
             Decimal('1650.00'), 20),

            ("خودکار سولر ڈرپ اریگیشن کٹ 30 گملے (Solar Automatic Drip Irrigation 30-Pot Kit)", 'TOOLS',
             "چھت اور بالکونی کے 30 گملوں کو خودکار طریقے سے وقت پر پانی دینے والا سولر پمپ اور ڈرپ پائپنگ سسٹم۔ (Solar-powered automated drip irrigation system supporting 30 individual planters with programmable timer.)",
             Decimal('4800.00'), 8),
        ]

        product_image_map = {
            "ریڈومل گولڈ": "products/ridomil_gold_fungicide_250g.jpg",
            "نیٹیوو": "products/nativo_fungicide_100g.jpg",
            "مووینٹو": "products/movento_systemic_insecticide.jpg",
            "کاپر آکسی کلورائیڈ": "products/copper_oxychloride_500g.jpg",
            "اوبیرون": "products/oberon_miticide_100ml.jpg",
            "پیلی چپکنے والی": "products/yellow_sticky_traps_pack20.jpg",
            "چلیٹڈ آئرن": "products/chelated_iron_eddha_250g.jpg",
            "سرسوں کی قدرتی": "products/mustard_oil_cake_powder_2kg.jpg",
            "اسٹیمڈ بون میل": "products/steamed_bone_meal_2kg.jpg",
            "پریمیئم کوکو پیٹ": "products/compressed_coco_peat_block_5kg.jpg",
            "پرلائٹ و ورمی کیولائٹ": "products/perlite_vermiculite_mix_3l.jpg",
            "سانپ پودا": "products/snake_plant_ceramic_pot.jpg",
            "5 لیٹر ہیوی ڈیوٹی": "products/5_liter_pressure_sprayer_pump.jpg",
            "3-ان-1 ڈیجیٹل": "products/3_in_1_soil_ph_moisture_meter.jpg",
            "خودکار سولر ڈرپ": "products/solar_drip_irrigation_kit_30pots.jpg",
        }

        for p in products:
            prod_obj, _ = Product.objects.get_or_create(
                seller=seller_profile,
                title=p[0],
                defaults={
                    'category': p[1],
                    'description': p[2],
                    'price': p[3],
                    'stock_quantity': p[4],
                    'status': 'APPROVED',
                }
            )
            for prefix, img_path in product_image_map.items():
                if prefix in prod_obj.title:
                    prod_obj.main_image = img_path
                    prod_obj.save(update_fields=['main_image'])
                    break

        self.stdout.write(f"  -> Successfully seeded {len(products)} marketplace agricultural products & tools.")

        # 7. Community Groups & Chat Rooms
        self.stdout.write("Seeding community groups and chat rooms...")
        grp1, _ = Group.objects.get_or_create(
            name="لاہور کچن گارڈننگ کلب (Lahore Kitchen Gardeners)",
            defaults={
                'description': 'لاہور اور گردونواح میں گھروں کی چھتوں پر سبزیاں اور پھل اگانے والے باغبانی کے شوقین افراد کا پلیٹ فارم۔',
                'city': 'Lahore',
                'latitude': Decimal('31.5204'),
                'longitude': Decimal('74.3587'),
                'creator': homeowner,
            }
        )
        GroupMembership.objects.get_or_create(group=grp1, user=homeowner)
        GroupMembership.objects.get_or_create(group=grp1, user=gardener)
        GroupMembership.objects.get_or_create(group=grp1, user=supervisor)

        # Community Chat Room
        cr_comm, _ = ChatRoom.objects.get_or_create(
            room_type='COMMUNITY',
            group=grp1,
            defaults={'name': 'لاہور کچن گارڈننگ برادری'}
        )
        Message.objects.get_or_create(
            room=cr_comm,
            sender=homeowner,
            content="السلام علیکم! کیا کسی بھائی نے سردیوں کے ٹماٹر کے بیج لگائے ہیں؟ کون سا وقت بہترین ہے؟"
        )
        Message.objects.get_or_create(
            room=cr_comm,
            sender=supervisor,
            content="وعلیکم السلام احمد بھائی! اکتوبر اور نومبر ٹماٹر کی پنیری لگانے کا بہترین وقت ہے۔ رات کی ٹھنڈ سے بچانے کے لیے پنیری کو کپڑے سے ڈھانپیں۔"
        )
        Message.objects.get_or_create(
            room=cr_comm,
            sender=homeowner,
            content="پودوں پر سفید مکھی اور لال مکڑی کا حملہ ہو رہا ہے، کوئی دیسی اور محفوظ نسخہ بتائیں؟"
        )
        Message.objects.get_or_create(
            room=cr_comm,
            sender=supervisor,
            content="نیم کا تیل 5 ملی لیٹر اور چند قطرے صابن 1 لیٹر نیم گرم پانی میں ملا کر ہر 4 دن بعد شام کو اسپرے کریں۔ ساتھ میں پیلی چپکنے والی شیٹس لگائیں۔"
        )

        # Garden Team Chat Room
        cr_team, _ = ChatRoom.objects.get_or_create(
            room_type='GARDEN_TEAM',
            garden=garden,
            defaults={'name': f"ٹیم چیٹ: {garden.name}"}
        )
        Message.objects.get_or_create(
            room=cr_team,
            sender=homeowner,
            content="علی مالی بھائی، گلاب کی کٹائی کے بعد پودوں کو کتنا پانی دینا ہے؟"
        )
        Message.objects.get_or_create(
            room=cr_team,
            sender=gardener,
            content="احمد صاحب، ابھی کھاد ڈالنے کے بعد ہلکا پانی دیا ہے۔ اگلے دو دن پانی نہ دیں تاکہ جڑیں کھاد کو اچھی طرح جذب کر لیں۔"
        )
        Message.objects.get_or_create(
            room=cr_team,
            sender=supervisor,
            content="علی مالی، لیموں کے پودے کے پتوں پر پیلا پن آ رہا ہے۔ کل چلیٹڈ آئرن (Fe-EDDHA) کا 5 گرام کا ہلکا محلول جڑوں میں دیجیے گا۔"
        )
        Message.objects.get_or_create(
            room=cr_team,
            sender=gardener,
            content="جی طارق صاحب، میں کل صبح کے وقت نم مٹی میں آئرن کا محلول دے دوں گا۔"
        )

        # Direct Chat Room (Buyer <-> Seller)
        cr_direct, _ = ChatRoom.objects.get_or_create(
            room_type='DIRECT',
            participant_one=homeowner,
            participant_two=seller_user,
            defaults={'name': f"{homeowner.username} اور {seller_user.username}"}
        )
        Message.objects.get_or_create(
            room=cr_direct,
            sender=homeowner,
            content="السلام علیکم بلال بھائی! کیا آپ کے پاس دیسی نیم آئل اور ریڈومل گولڈ کا پیکٹ دستیاب ہے؟"
        )
        Message.objects.get_or_create(
            room=cr_direct,
            sender=seller_user,
            content="وعلیکم السلام! جی بالکل، تازہ تیار شدہ نیم آئل اور ریڈومل گولڈ فنگسائیڈ وافر مقدار میں اسٹاک میں موجود ہے۔ آپ کیش آن ڈیلیوری آرڈر کر سکتے ہیں۔"
        )

        self.stdout.write(self.style.SUCCESS("Baghbaan AI database successfully seeded with all sample entities!"))
