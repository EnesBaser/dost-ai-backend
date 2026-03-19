"""
Learning Engine v2.0
Extracts user facts, interests, personality from conversations
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

class LearningEngine:
    """AI Learning Engine for user personalization"""
    
    # Interest categories and keywords
    INTEREST_PATTERNS = {
        'sports': {
            'teams': {
                'fenerbahçe|fener|fb': 'team:fenerbahce',
                'galatasaray|gs|cimbom': 'team:galatasaray',
                'beşiktaş|bjk|kartal': 'team:besiktas',
                'trabzonspor|ts': 'team:trabzonspor',
            },
            'keywords': ['maç', 'gol', 'futbol', 'basketbol', 'voleybol', 'şampiyonluk']
        },
        'cinema': {
            'genres': {
                'aksiyon|action': 'genre:action',
                'komedi|comedy': 'genre:comedy',
                'korku|horror': 'genre:horror',
                'drama': 'genre:drama',
                'bilim kurgu|sci-fi': 'genre:scifi',
            },
            'keywords': ['film', 'sinema', 'dizi', 'netflix', 'izledim', 'seyrettim']
        },
        'theater': {
            'keywords': ['tiyatro', 'oyun', 'sahne', 'müzikal', 'gösteri']
        },
        'music': {
            'genres': {
                'rock': 'genre:rock',
                'pop': 'genre:pop',
                'rap|hiphop': 'genre:hiphop',
                'klasik': 'genre:classical',
                'caz|jazz': 'genre:jazz',
            },
            'keywords': ['müzik', 'şarkı', 'konser', 'dinliyorum', 'playlist']
        },
        'food': {
            'keywords': ['yemek', 'restoran', 'lezzetli', 'aç', 'yedim', 'içtim', 'kahve']
        },
        'technology': {
            'keywords': ['kod', 'programlama', 'yazılım', 'teknoloji', 'ai', 'yapay zeka']
        },
        'travel': {
            'keywords': ['gezi', 'tatil', 'seyahat', 'yolculuk', 'uçak', 'otel']
        },
        'books': {
            'keywords': ['kitap', 'okuyorum', 'roman', 'öykü', 'yazar']
        }
    }
    
    # Location patterns
    LOCATION_PATTERNS = {
        'cities': {
            'istanbul': 'city:istanbul',
            'ankara': 'city:ankara',
            'izmir': 'city:izmir',
            'bursa': 'city:bursa',
            'antalya': 'city:antalya',
        },
        'districts': {
            'kadıköy': 'district:kadikoy',
            'beşiktaş': 'district:besiktas',
            'şişli': 'district:sisli',
            'beyoğlu': 'district:beyoglu',
        }
    }
    
    # ============================================
    # ETHİCAL FİLTERS & FORBIDDEN PATTERNS
    # ============================================
    
    # ASLA saklanmaması gereken bilgiler
    FORBIDDEN_PATTERNS = {
        'race_ethnicity': ['ırk', 'soy', 'etnik', 'ten rengi'],
        'religion_specific': ['müslüman', 'hristiyan', 'yahudi', 'budist', 'ateist'],  # Genel din ilgisi OK, spesifik üyelik NO
        'political_party': ['akp', 'chp', 'mhp', 'hdp', 'parti üyesi'],  # Politik ilgi OK, üyelik NO
        'sexual_orientation': ['eşcinsel', 'heteroseksüel', 'biseksüel', 'lgbtq'],
        'health_conditions': ['kanser', 'diyabet', 'depresyon', 'hastalık', 'tedavi'],
        'financial_details': ['maaş', 'banka hesap', 'kredi kartı', 'borç miktarı'],
        'illegal_activity': ['uyuşturucu', 'hırsızlık', 'yasadışı', 'kaçak'],
        'violence': ['şiddet', 'dövmek', 'kavga', 'zarar vermek'],
        'discrimination': ['ayrımcılık', 'nefret', 'hor görmek', 'aşağılamak']
    }
    
    # Hassas ama context'e göre saklanabilir (sadece yardım/destek için)
    SENSITIVE_PATTERNS = {
        'mental_health_support': ['üzgün', 'mutsuz', 'yalnız', 'moral bozuk'],  # Destek için OK
        'substance_awareness': ['sigara', 'alkol'],  # Sadece farkındalık için
        'relationship_status': ['bekar', 'evli', 'ayrıldım']  # Genel durum OK
    }
    
    # Kültürel hassasiyet (Türkiye)
    CULTURAL_RESPECT = {
        'religious_periods': ['ramazan', 'bayram', 'kurban', 'şeker bayramı'],
        'cultural_values': ['aile', 'saygı', 'büyük', 'küçük', 'hürmet'],
        'local_traditions': ['kabak tatlısı', 'helva', 'lokum', 'çay']
    }
    
    # Personality indicators (Expanded v2.0)
    PERSONALITY_INDICATORS = {
        # Sosyal Eğilimler
        'social': ['arkadaş', 'sosyal', 'takılıyorum', 'buluşma', 'kalabalık', 'dışarı çık', 'parti'],
        'introvert': ['içe dönük', 'yalnız', 'sessiz', 'sakin', 'kendi halinde', 'tek başına'],
        'extrovert': ['dışa dönük', 'konuşkan', 'canlı', 'enerjik', 'topluluk', 'gürültü'],
        
        # Aktivite Düzeyi
        'active': ['spor', 'hareket', 'aktif', 'yürüyüş', 'koşu', 'jimnastik', 'bisiklet'],
        'lazy': ['tembel', 'üşenmek', 'yatmak', 'uyumak', 'hareketsiz', 'oturmak'],
        'energetic': ['enerjik', 'dinç', 'hareketli', 'yorulmak bilmez', 'canlı'],
        
        # Duygusal Yapı
        'emotional': ['duygusal', 'hassas', 'empatik', 'hissetmek', 'ağlamak', 'kırılgan'],
        'logical': ['mantıklı', 'akılcı', 'rasyonel', 'analitik', 'objektif', 'akıl'],
        'optimistic': ['iyimser', 'olumlu', 'umutlu', 'pozitif', 'güzel görmek'],
        'pessimistic': ['kötümser', 'karamsar', 'endişeli', 'negatif', 'korkulu'],
        'calm': ['sakin', 'huzurlu', 'rahat', 'dingin', 'stressiz', 'soğukkanlı'],
        'anxious': ['endişeli', 'kaygılı', 'stresli', 'gergin', 'telaşlı', 'panik'],
        
        # Yaratıcılık & Düşünce
        'creative': ['yaratıcı', 'sanat', 'müzik', 'resim', 'yazı', 'hayal', 'orijinal'],
        'intellectual': ['öğrenmek', 'araştırma', 'kitap', 'bilgi', 'merak', 'fikir', 'düşünmek'],
        'practical': ['pratik', 'gerçekçi', 'uygulamacı', 'somut', 'işe yarar'],
        'philosophical': ['felsefi', 'derin', 'anlam', 'varoluş', 'düşünce', 'sorgulamak'],
        
        # Davranış Tarzı
        'organized': ['düzenli', 'planlı', 'tertipli', 'organize', 'sistemli', 'program'],
        'spontaneous': ['spontane', 'anlık', 'plansız', 'ani', 'rastgele', 'doğaçlama'],
        'perfectionist': ['mükemmeliyetçi', 'detaycı', 'titiz', 'kusursuz', 'eksiksiz'],
        'flexible': ['esnek', 'uyumlu', 'adapte', 'değişken', 'ayak uydurmak'],
        
        # Motivasyon & Hedefler
        'ambitious': ['hırslı', 'azimli', 'hedef odaklı', 'başarılı', 'kazanmak', 'zirve'],
        'relaxed': ['rahat', 'sakin', 'takılmayan', 'gevşek', 'bırakmak'],
        'competitive': ['rekabetçi', 'yarışmacı', 'kazanmak', 'birinci', 'üstün'],
        'cooperative': ['işbirlikçi', 'yardımsever', 'birlikte', 'paylaşmak', 'takım'],
        
        # Macera & Risk
        'adventurous': ['macera', 'yeni', 'keşfetmek', 'deneyim', 'risk', 'cesur', 'atılgan'],
        'cautious': ['temkinli', 'dikkatli', 'ihtiyatlı', 'güvenli', 'tedbirli'],
        'risk_taker': ['risk almak', 'cesaret', 'atlamak', 'denemek', 'tehlike'],
        
        # Yaşam Tarzı
        'homebody': ['ev', 'rahat', 'huzur', 'dinlenmek', 'uyku', 'evde kalmak'],
        'outdoor': ['dışarı', 'açık hava', 'doğa', 'gezinti', 'bahçe'],
        'minimalist': ['minimal', 'sade', 'basit', 'az', 'yalın'],
        'maximalist': ['bol', 'çok', 'zengin', 'renkli', 'dolu'],
        
        # İletişim Tarzı
        'communicative': ['konuşkan', 'anlatmak', 'paylaşmak', 'söylemek', 'iletişim'],
        'reserved': ['çekingen', 'ketum', 'az konuş', 'gizli', 'içine kapanık'],
        'direct': ['direkt', 'açık', 'net', 'doğrudan', 'samimi'],
        'diplomatic': ['diplomatik', 'nazik', 'kibar', 'yumuşak', 'tatlı dilli'],
        
        # Öğrenme & Gelişim
        'curious': ['meraklı', 'soru sormak', 'öğrenmek', 'keşfetmek', 'araştırmak'],
        'traditional': ['geleneksel', 'klasik', 'eski usul', 'alışılmış', 'standart'],
        'innovative': ['yenilikçi', 'modern', 'ileri görüşlü', 'farklı', 'değişim'],
        
        # Sorumluluk & Disiplin
        'responsible': ['sorumlu', 'güvenilir', 'disiplinli', 'ödevini yapmak', 'ciddi'],
        'carefree': ['kaygısız', 'özgür', 'serbest', 'dert yok', 'takılmamak'],
        'disciplined': ['disiplinli', 'kurallı', 'düzenli', 'kararlı', 'tutarlı'],
        
        # Empati & İlişkiler
        'empathetic': ['empatik', 'anlayışlı', 'şefkatli', 'merhametli', 'duyarlı'],
        'independent': ['bağımsız', 'özgür', 'kendi başına', 'tek başına', 'muhtaç değil'],
        'supportive': ['destekleyici', 'yardımsever', 'arkadaş canlısı', 'iyilik'],
        
        # Özgüven & Benlik
        'confident': ['kendine güvenen', 'özgüvenli', 'emin', 'kararlı', 'güçlü'],
        'humble': ['alçakgönüllü', 'mütevazı', 'sade', 'gösterişsiz', 'kibar'],
        'assertive': ['kararlı', 'iddialı', 'güçlü', 'kesin', 'sert']
    }
    
    @staticmethod
    def is_ethical(message: str, category: str = None) -> bool:
        """
        Check if message content is ethical to store
        Returns False if content matches forbidden patterns
        """
        message_lower = message.lower()
        
        # Check forbidden patterns
        for pattern_type, keywords in LearningEngine.FORBIDDEN_PATTERNS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Log blocked pattern for monitoring (production-safe)
                    return False
        
        # All clear!
        return True
    
    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to slug format"""
        import re
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '_', text)
        return text.strip('_')
    
    @staticmethod
    def extract_sports_team_dynamic(message: str) -> Optional[Dict]:
        """
        Dinamik takım çıkarma - HERHANGİ BİR TAKIMI yakalar!
        Elazığspor, Kırklarelispor, Manchester United, vs.
        """
        import re
        message_lower = message.lower()
        
        patterns = [
            (r'(\w+spor)\s*(taraftar|tutuyor|sever|destekl|maç)', 0.9),  # Elazığspor taraftarıyım
            (r'(\w+)\s*takımını?\s*(tutuyor|destekl|sever)', 0.85),      # Barcelona takımını tutuyorum
            (r'(\w+)\s*(fb|gs|bjk|ts|sk)\s*(taraftar|maç)', 0.9),        # Kısaltmalar
            (r'(\w+lı)\s*takım', 0.8),                                    # Ankaralı takım
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                team_name = match.group(1)
                # Çok kısa isimleri filtrele (örn: "bir", "çok")
                if len(team_name) < 3:
                    continue
                    
                return {
                    'category': 'sports',
                    'fact_key': f'team:{LearningEngine.slugify(team_name)}',
                    'fact_value': team_name.title(),
                    'confidence': confidence,
                    'source': 'conversation'
                }
        return None
    
    @staticmethod
    def extract_sport_type_dynamic(message: str) -> Optional[Dict]:
        """
        Dinamik spor dalı çıkarma - Dağcılık, yüzme, tenis, yoga, vs.
        """
        import re
        message_lower = message.lower()
        
        patterns = [
            (r'(\w+lık)\s*(yapıyor|sever|ilgilen|oynuyor)', 0.85),  # dağcılık yapıyorum
            (r'(\w+)\s*sporu\s*(yapıyor|sever|oynuyor)', 0.9),      # tenis sporu yapıyorum
            (r'(\w+)\s*(oynuyor|yapıyor|antrenman)', 0.8),          # voleybol oynuyorum
        ]
        
        # Bilinen spor dalları (yüksek confidence için)
        known_sports = {
            'futbol', 'basketbol', 'voleybol', 'tenis', 'yüzme', 'koşu',
            'dağcılık', 'bisiklet', 'yoga', 'pilates', 'kick boks', 'karate',
            'tekvando', 'judo', 'güreş', 'halter', 'atletizm', 'golf',
            'badminton', 'masa tenisi', 'boks', 'eskrim', 'okçuluk'
        }
        
        for pattern, base_confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                sport = match.group(1)
                
                # Çok kısa isimleri filtrele
                if len(sport) < 3:
                    continue
                
                # Bilinen sporsa confidence artır
                confidence = base_confidence + 0.1 if sport in known_sports else base_confidence
                
                return {
                    'category': 'sports',
                    'fact_key': f'sport:{LearningEngine.slugify(sport)}',
                    'fact_value': sport.title(),
                    'confidence': min(confidence, 0.95),
                    'source': 'conversation'
                }
        return None
    
    @staticmethod
    def extract_location_dynamic(message: str) -> Optional[Dict]:
        """
        Dinamik şehir/ilçe çıkarma - HERHANGİ BİR ŞEHİR/İLÇEYİ yakalar!
        Elazığ, Malatya, Diyarbakır, vs.
        """
        import re
        message_lower = message.lower()
        
        patterns = [
            (r'(\w+)\'?d[ae]\s*(yaşı|otur|bulun|ev)', 0.95),     # Elazığ'da yaşıyorum
            (r'(\w+)\'?l[iıİI]y?[iıİI]m', 0.9),                  # İstanbulluyum
            (r'(\w+)\s*(?:şehir|il)inde', 0.85),                 # Ankara şehrinde
            (r'(\w+)\s*(?:ilçe|semtinde)', 0.85),                # Kadıköy ilçesinde
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                location = match.group(1)
                
                # Çok kısa isimleri filtrele
                if len(location) < 3:
                    continue
                
                # Yaygın kelimelerle karışmasın
                common_words = ['bir', 'şu', 'bu', 'çok', 'var', 'yok', 'ben', 'sen']
                if location in common_words:
                    continue
                
                return {
                    'category': 'location',
                    'fact_key': f'city:{LearningEngine.slugify(location)}',
                    'fact_value': location.title(),
                    'confidence': confidence,
                    'source': 'conversation'
                }
        return None
    
    @staticmethod
    def extract_hobby_dynamic(message: str) -> Optional[Dict]:
        """
        Dinamik hobi çıkarma - Resim, müzik aleti, koleksiyon, vs.
        """
        import re
        message_lower = message.lower()
        
        patterns = [
            (r'(\w+)\s*(?:koleksiyonu|koleksiyon|topluyor)', 0.9),  # pul koleksiyonu
            (r'(\w+)\s*(?:çalmak|çalıyor|çalışıyor)', 0.85),        # gitar çalıyorum
            (r'(\w+)\s*(?:yapmak|yapmayı)\s*sever', 0.85),          # bahçecilik yapmayı severim
            (r'(\w+)\s*(?:hobi|ilgi alan|merak)', 0.8),             # fotoğrafçılık hobim
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                hobby = match.group(1)
                
                if len(hobby) < 3:
                    continue
                
                return {
                    'category': 'hobbies',
                    'fact_key': f'hobby:{LearningEngine.slugify(hobby)}',
                    'fact_value': hobby.title(),
                    'confidence': confidence,
                    'source': 'conversation'
                }
        return None
    
    @staticmethod
    def extract_profession_dynamic(message: str) -> Optional[Dict]:
        """
        Dinamik meslek çıkarma - Öğretmen, mühendis, doktor, vs.
        """
        import re
        message_lower = message.lower()
        
        patterns = [
            (r'(\w+)\s*(?:olarak çalış|mesleğ)', 0.95),  # öğretmen olarak çalışıyorum
            (r'(\w+)(?:im|ım|um|üm)\s*(?:ve|,)', 0.9),   # mühendisim ve
            (r'ben\s*(?:bir\s*)?(\w+)', 0.85),            # ben bir doktorum
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                profession = match.group(1)
                
                if len(profession) < 4:
                    continue
                
                return {
                    'category': 'career',
                    'fact_key': f'profession:{LearningEngine.slugify(profession)}',
                    'fact_value': profession.title(),
                    'confidence': confidence,
                    'source': 'conversation'
                }
        return None
    
    @staticmethod
    def extract_interests(message: str) -> List[Dict]:
        """Extract interests from message - STATIC + DYNAMIC"""
        message_lower = message.lower()
        interests = []
        
        # 1. DYNAMIC EXTRACTORS (Öncelik!)
        # Takım dinamik
        dynamic_team = LearningEngine.extract_sports_team_dynamic(message)
        if dynamic_team:
            interests.append(dynamic_team)
        
        # Spor dalı dinamik
        dynamic_sport = LearningEngine.extract_sport_type_dynamic(message)
        if dynamic_sport:
            interests.append(dynamic_sport)
        
        # Hobi dinamik
        dynamic_hobby = LearningEngine.extract_hobby_dynamic(message)
        if dynamic_hobby:
            interests.append(dynamic_hobby)
        
        # Meslek dinamik
        dynamic_profession = LearningEngine.extract_profession_dynamic(message)
        if dynamic_profession:
            interests.append(dynamic_profession)
        
        # 2. STATIC PATTERNS (Yedek - bilinen kategoriler için)
        for category, patterns in LearningEngine.INTEREST_PATTERNS.items():
            # Check keywords
            if 'keywords' in patterns:
                for keyword in patterns['keywords']:
                    if keyword in message_lower:
                        interests.append({
                            'category': category,
                            'fact_key': f'interest:{category}',
                            'confidence': 0.7,
                            'source': 'conversation'
                        })
                        break
            
            # Check specific items (teams, genres, etc) - artık dynamic yeterli ama yedek olsun
            if 'teams' in patterns:
                for pattern, fact_key in patterns['teams'].items():
                    if re.search(pattern, message_lower):
                        # Sadece dynamic bulamadıysa ekle
                        if not dynamic_team:
                            interests.append({
                                'category': category,
                                'fact_key': fact_key,
                                'confidence': 0.9,
                                'source': 'conversation'
                            })
            
            if 'genres' in patterns:
                for pattern, fact_key in patterns['genres'].items():
                    if re.search(pattern, message_lower):
                        interests.append({
                            'category': category,
                            'fact_key': fact_key,
                            'confidence': 0.8,
                            'source': 'conversation'
                        })
        
        return interests
    
    @staticmethod
    def extract_location(message: str) -> Optional[Dict]:
        """Extract location from message - DYNAMIC FIRST!"""
        message_lower = message.lower()
        
        # 1. DYNAMIC EXTRACTION (Öncelik!)
        dynamic_location = LearningEngine.extract_location_dynamic(message)
        if dynamic_location:
            return dynamic_location
        
        # 2. STATIC PATTERNS (Yedek - bilinen şehirler için)
        # Check cities
        for city, fact_key in LearningEngine.LOCATION_PATTERNS['cities'].items():
            if city in message_lower:
                return {
                    'category': 'location',
                    'fact_key': fact_key,
                    'confidence': 0.9,
                    'source': 'conversation'
                }
        
        # Check districts
        for district, fact_key in LearningEngine.LOCATION_PATTERNS['districts'].items():
            if district in message_lower:
                return {
                    'category': 'location',
                    'fact_key': fact_key,
                    'confidence': 0.85,
                    'source': 'conversation'
                }
        
        return None
    
    @staticmethod
    def infer_personality(message: str) -> List[Dict]:
        """Infer personality traits from message"""
        message_lower = message.lower()
        traits = []
        
        for trait, indicators in LearningEngine.PERSONALITY_INDICATORS.items():
            matches = sum(1 for indicator in indicators if indicator in message_lower)
            
            if matches > 0:
                confidence = min(0.5 + (matches * 0.1), 0.9)
                traits.append({
                    'trait': trait,
                    'score': confidence,
                    'evidence_count': matches
                })
        
        return traits
    
    @staticmethod
    def analyze_message(message: str) -> Dict:
        """Complete analysis of a message"""
        
        # Ethical filter FIRST!
        if not LearningEngine.is_ethical(message):
            return {
                'interests': [],
                'location': None,
                'personality': [],
                'timestamp': datetime.now().isoformat(),
                'filtered': True  # Indicates content was filtered
            }
        
        return {
            'interests': LearningEngine.extract_interests(message),
            'location': LearningEngine.extract_location(message),
            'personality': LearningEngine.infer_personality(message),
            'timestamp': datetime.now().isoformat(),
            'filtered': False
        }
    
    @staticmethod
    def generate_personalized_prompt(user_facts: List[Dict], message: str) -> str:
        """Generate personalized system prompt based on user facts"""
        
        # Group facts by category
        facts_by_category = {}
        for fact in user_facts:
            category = fact['category']
            if category not in facts_by_category:
                facts_by_category[category] = []
            facts_by_category[category].append(fact)
        
        # Build context
        context_parts = ["You are DostAI, a personalized AI companion."]
        
        # Add user interests
        if 'sports' in facts_by_category:
            teams = [f['fact_key'].split(':')[1] for f in facts_by_category['sports'] if 'team:' in f['fact_key']]
            if teams:
                context_parts.append(f"User is a fan of: {', '.join(teams)}.")
        
        if 'cinema' in facts_by_category:
            context_parts.append("User enjoys watching movies.")
        
        if 'theater' in facts_by_category:
            context_parts.append("User is interested in theater and performing arts.")
        
        # Add location
        if 'location' in facts_by_category:
            locations = [f['fact_key'].split(':')[1] for f in facts_by_category['location']]
            if locations:
                context_parts.append(f"User is located in: {', '.join(locations)}.")
        
        # Combine with original message
        personalized_prompt = "\n".join(context_parts)
        personalized_prompt += f"\n\nUser message: {message}"
        
        return personalized_prompt


# ================================================
# EXAMPLE USAGE
# ================================================

if __name__ == "__main__":
    # Test messages
    test_messages = [
        "Fenerbahçe maçını izledim, harika gol attı!",
        "Kadıköy'de yeni bir sinema açılmış, aksiyon filmi izleyeceğim",
        "Tiyatro oyununa gitmek istiyorum bu hafta sonu",
        "Rock müzik dinlemeyi seviyorum, konser var mı?",
    ]
    
    print("=== LEARNING ENGINE TEST ===\n")
    
    for msg in test_messages:
        print(f"Message: {msg}")
        analysis = LearningEngine.analyze_message(msg)
        print(f"Analysis: {analysis}\n")
    
    # Test personalized prompt
    print("\n=== PERSONALIZED PROMPT TEST ===\n")
    
    sample_facts = [
        {'category': 'sports', 'fact_key': 'team:fenerbahce', 'confidence': 0.9},
        {'category': 'cinema', 'fact_key': 'genre:action', 'confidence': 0.8},
        {'category': 'location', 'fact_key': 'city:istanbul', 'confidence': 1.0},
    ]
    
    prompt = LearningEngine.generate_personalized_prompt(
        sample_facts, 
        "Bu hafta sonu ne yapsam?"
    )
    print(prompt)
