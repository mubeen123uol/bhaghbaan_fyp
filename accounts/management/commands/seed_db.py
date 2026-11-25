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

        # 2. Curated Pakistani Plants (40+ Species)
        self.stdout.write("Seeding 40+ Pakistani indigenous and common home garden plants...")
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

            ("Money Plant", "منی پلانٹ", "Money Plant", "Epipremnum aureum", "ORNAMENTAL",
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

            ("Aloe Vera / Ghee Kawar", "ایلوویرا (گھیگوار)", "Aloe Vera", "Aloe barbadensis miller", "SUCCULENT",
             "Succulent with medicinal gel for skin burns, hair care, and digestion.",
             "موٹے گودے دار پتوں والا سخت جان پودا جس کا جیل جلد کی خوبصورتی، جلنے اور بالوں کے لیے لاجواب ہے۔",
             7, 90, "None", "Indirect Bright Sun", True, "Overwatering kills Aloe Vera; let soil dry completely between waterings."),

            ("Adrak / Ginger", "ادرک", "Adrak", "Zingiber officinale", "HERB",
             "Underground aromatic rhizome cultivated in moist, shaded garden planters.",
             "کھانوں اور قہووں میں روزانہ استعمال ہونے والی جڑ۔ نرم بھل والی مٹی اور جزوی چھاؤں میں اچھی اگتی ہے۔",
             2, 30, "Monsoon", "Partial Shade", False, "Harvest after 8-10 months when leaves turn yellow."),

            ("Lehsan / Garlic", "لہسن", "Lehsan", "Allium sativum", "VEGETABLE",
             "Pungent winter bulb that doubles as a companion plant repelling pests.",
             "سرما کی مشہور فصل۔ گملوں میں لونگیں دبا کر آسانی سے اگایا جاتا ہے، کیڑوں کو دور بھگاتا ہے۔",
             3, 30, "Winter", "Full Sun", False, "Plant cloves in October/November for a bountiful April harvest."),

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

            ("Falsa", "فالسہ", "Falsa", "Grewia asiatica", "FRUIT",
             "Tangy cooling purple summer berries used for iconic Pakistani summer sherbets.",
             "گرمیوں کی شدت توڑنے والا ترش و میٹھا پھل جس کا شربت پاکستان بھر میں مقبول ہے۔",
             3, 45, "Severe Winter Pruning", "Full Sun", False, "Hard winter pruning down to 3-4 feet ensures huge crop of sweet berries."),

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

        created_plants = []
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
            created_plants.append(obj)

        self.stdout.write(f"  -> Successfully seeded {len(created_plants)} botanical plant profiles.")

        # 3. Diseases and Treatments
        self.stdout.write("Seeding plant diseases and treatment protocols...")
        diseases_data = [
            ("Safaid Makhi (Whitefly)", "سفید مکھی کا حملہ", "Safaid Makhi", "Bemisia tabaci", "HIGH",
             "Tiny white flies under leaves, yellowing of leaves, sooty black mold formation, sticky honeydew.",
             "پتوں کے نیچے سفید رنگ کی باریک مکھیاں اڑتی ہوئی نظر آتی ہیں۔ پتے پیلے پڑ جاتے ہیں اور ان پر کالی پھپھوندی جم جاتی ہے۔",
             "Spray 5ml organic Neem oil mixed with 2ml liquid soap in 1L water every 4 days. In severe cases, apply Imidacloprid (Confidor) at 1ml per liter.",
             "ایک لیٹر پانی میں 5 ملی لیٹر نیم کا تیل اور چند قطرے برتن دھونے والا صابن ملا کر شام کے وقت پتوں کے نیچے اسپرے کریں۔ شدید حملے پر ایمیڈاکلوپرڈ (کانفیڈور) 1 ملی لیٹر فی لیٹر کے حساب سے اسپرے کریں۔",
             "کیمیائی اسپرے کرتے وقت ماسک اور دستانے پہنیں۔ پھل اور سبزی اسپرے کے 7 دن بعد تک استعمال نہ کریں۔"),

            ("Powdery Mildew / Safaid Phaphondi", "سفید پھپھوندی (پاؤڈری ملڈیو)", "Safaid Phaphondi", "Erysiphe cichoracearum", "MEDIUM",
             "White talcum powder-like spots appearing on upper leaf surfaces and buds, causing leaf curling and drying.",
             "پتوں کی اوپری سطح پر سفید ٹیلکم پاؤڈر جیسے دھبے نمودار ہوتے ہیں جس سے پتے مڑ کر خشک ہونے لگتے ہیں۔",
             "Mix 1 part cow milk with 9 parts water and spray in morning sun. For fungicide, apply Wettable Sulphur or Score (Difenoconazole).",
             "ایک حصہ گائے کا دودھ 9 حصے پانی میں ملا کر صبح کی دھوپ میں اسپرے کریں۔ دیسی لکڑی کی باریک راکھ چھڑکیں۔ کیمیائی علاج میں سلفر پاؤڈر یا اسکور فنگسائیڈ اسپرے کریں۔",
             "تیز دھوپ اور دوپہر کے وقت سلفر اسپرے نہ کریں ورنہ پتے جل سکتے ہیں۔"),

            ("Leaf Curl Virus / Marorha Rog", "پتہ مروڑ وائرس (مروڑھا روگ)", "Patta Marorha", "Chilli leaf curl virus", "CRITICAL",
             "Leaves curling upwards like a boat, stunted plant growth, thickening of veins, brittle foliage.",
             "پتے کشتی نما اوپر کی طرف مڑ جاتے ہیں، پودے کا قد چھوٹا رہ جاتا ہے اور نئی کونپلیں بننا رک جاتی ہیں۔",
             "Transmit by whitefly; eliminate vectors using yellow sticky traps and neem spray. Rogue out and burn heavily stunted plants.",
             "یہ وائرس سفید مکھی سے پھیلتا ہے۔ پیلے چپکنے والے کارڈز لگائیں اور بیمار پودوں کو اکھاڑ کر دور دبا دیں تاکہ دوسرے پودے محفوظ رہیں۔",
             "وائرس کا کوئی براہ راست کیمیائی علاج نہیں ہے؛ صرف سفید مکھی کو مار کر اس کا پھیلاؤ روکا جا سکتا ہے۔"),

            ("Susti Kida / Aphids", "سست کیڑا (تیلا)", "Sust Kida / Tela", "Aphis gossypii", "MEDIUM",
             "Clusters of tiny green/black insects sucking sap on tender new shoots and buds.",
             "نرم کونپلوں اور کلیوں پر سبز اور سیاہ رنگ کے ننھے کیڑوں کا جمگھٹا جو پودے کا رس چوستے ہیں۔",
             "Blast with strong water jet from garden hose. Spray garlic-chilli tea or mild soapy water.",
             "تیز پانی کی دھار سے کیڑوں کو دھو دیں۔ لہسن اور ہری مرچ کو پانی میں پکا کر چھان لیں اور پودے پر اسپرے کریں۔",
             "شام کے وقت اسپرے کریں تاکہ مفید کیڑے (لیڈی برڈ بیٹل) محفوظ رہیں۔"),

            ("Jad Ki Saran / Root Rot", "جڑوں کی سڑن (روٹ راٹ)", "Jad ki Saran", "Fusarium / Pythium", "HIGH",
             "Wilting of whole plant despite moist soil, blackened mushy decaying roots, foul damp odor.",
             "مٹی میں نمی کے باوجود پودا مرجھا جاتا ہے، گملے سے پودا نکالنے پر جڑیں سیاہ، نرم اور بدبودار نکلتی ہیں۔",
             "Immediately stop watering. Repot into fresh well-draining bhal soil mixed with river sand. Drench root zone with Carbendazim (Derosal) fungicide.",
             "فوری طور پر پانی دینا بند کریں۔ پودے کو گملے سے نکال کر سڑی ہوئی جڑیں کاٹیں اور تازہ بھل و ریتلی مٹی میں لگائیں۔ کاربینڈازم فنگسائیڈ کا محلول جڑوں میں ڈالیں۔",
             "گملے کے پیندے میں نکاسی کا سوراخ ہمیشہ کھلا رکھیں۔ ضرورت سے زیادہ پانی پودے کا سب سے بڑا دشمن ہے۔"),
        ]

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
            # Link to sample plants
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
                    'instructions_en': d[7],
                    'instructions_ur': d[8],
                    'safety_disclaimer_ur': d[9],
                }
            )

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
        mint_template = Plant.objects.filter(name_roman__icontains='Pudina').first()

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

        # 6. Marketplace Products
        self.stdout.write("Seeding verified nursery products in marketplace...")
        products = [
            ("خالص دیسی نیم کا تیل (Pure Organic Neem Oil 500ml)", 'PESTICIDE',
             "100% خالص ٹھنڈے طریقہ کار سے تیار شدہ نیم آئل۔ سفید مکھی، تیلا اور پاؤڈری ملڈیو کا قدرتی دشمن۔ پودوں کے لیے بے ضرر۔",
             Decimal('650.00'), 45),
            
            ("نامیاتی گلی سڑی گوبر کھاد (Organic Aged Compost 10kg)", 'FERTILIZER',
             "دو سال پرانی تیار شدہ دیسی کھاد جو مٹی کی زرخیزی اور پھولوں کے سائز میں فوری اضافہ کرتی ہے۔ بالکل بو کے بغیر۔",
             Decimal('400.00'), 80),
             
            ("دیسی لال گلاب کا تیار پودا (Desi Red Rose in 12-inch Pot)", 'PLANTS',
             "خوشبودار دیسی سرخ گلاب کا تندرست اور کلیوں سے لدا پودا، مٹی کے پکے گملے میں تیار شدہ۔",
             Decimal('350.00'), 25),
             
            ("کاغذی لیموں کا پیوندی پودا (Grafted Kaghzi Lemon Plant)", 'PLANTS',
             "دو سالہ پیوندی لیموں کا پودا جو پہلے سال سے ہی وافر پھل دینا شروع کر دیتا ہے۔",
             Decimal('850.00'), 20),

            ("پریمیئم کچن گارڈن بیج پیکٹ 10 اقسام (Winter Kitchen Garden Seeds)", 'SEEDS',
             "ٹماٹر، ہری مرچ، پالک، دھنیا، مولی، گاجر، بینگن، سلاد پتہ، میتھی اور مٹر کے اعلیٰ جرمنیشن والے بیج۔",
             Decimal('750.00'), 60),

            ("روایتی مٹی کے پکے گملے (14-inch Terracotta Clay Pots)", 'POTS',
             "گجرات کے روایتی مٹی کے بنے ہوئے پکے گملے جن میں پودوں کی جڑیں ٹھنڈی رہتی ہیں اور ہوا کا گزر ہوتا ہے۔",
             Decimal('280.00'), 50),

            ("باغبانی کٹر اور کانٹ چھانٹ قینچی (Heavy Duty Garden Pruning Shears)", 'TOOLS',
             "سٹین لیس سٹیل کا تیز دھار کٹر جو پودوں کی شاخوں کو بغیر نقصان پہنچائے صفائی سے کاٹتا ہے۔",
             Decimal('1200.00'), 15),

            ("این پی کے متوازن کھاد (Balanced NPK 20-20-20 Fertilizer 1kg)", 'FERTILIZER',
             "پودوں کی مجموعی بڑھوتری، سبز پتوں اور بھرپور پھولوں کے لیے پانی میں حل پذیر معیاری کھاد۔",
             Decimal('950.00'), 30),
        ]

        for p in products:
            Product.objects.get_or_create(
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
            content="السلام علیکم بلال بھائی! کیا آپ کے پاس دیسی نیم آئل کا 500ml کا پیکٹ دستیاب ہے؟"
        )
        Message.objects.get_or_create(
            room=cr_direct,
            sender=seller_user,
            content="وعلیکم السلام! جی بالکل، تازہ تیار شدہ نیم آئل وافر مقدار میں اسٹاک میں موجود ہے۔ آپ کیش آن ڈیلیوری آرڈر کر سکتے ہیں۔"
        )

        self.stdout.write(self.style.SUCCESS("Baghbaan AI database successfully seeded with all sample entities!"))
