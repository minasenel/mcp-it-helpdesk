# Web-based IT Help Desk Agent

Bu proje, FastAgent'ınızı web tarayıcısında kullanmanızı sağlayan modern bir web arayüzü sağlar.

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Yükleyin
```bash
pip install -e .
```

### 2. Web Arayüzünü Başlatın
```bash
python start_web_agent.py
```

veya doğrudan:

```bash
python web_agent.py
```

### 3. Tarayıcınızda Açın
Web tarayıcınızda şu adrese gidin: http://localhost:5000

## 🎯 Özellikler

- **Modern Web Arayüzü**: Responsive tasarım, güzel görünüm
- **Gerçek Zamanlı Chat**: WebSocket ile anlık mesajlaşma
- **IT Help Desk Desteği**: Teknik sorunlar için özelleştirilmiş agent
- **MCP Entegrasyonu**: Mevcut MCP sunucularınızla tam uyumluluk
- **Mobil Uyumlu**: Tüm cihazlarda çalışır

## 🛠️ Teknik Detaylar

### Kullanılan Teknolojiler
- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
- **Real-time Communication**: WebSocket
- **Agent Integration**: FastAgent Python API

### Dosya Yapısı
```
├── web_agent.py          # Ana web uygulaması
├── start_web_agent.py    # Başlatma scripti
├── templates/
│   └── index.html        # Web arayüzü
└── static/               # CSS/JS dosyaları (gerekirse)
```

## 🔧 Yapılandırma

Web arayüzü, mevcut `fastagent.config.yaml` dosyanızı kullanır. Agent yapılandırmasını değiştirmek için bu dosyayı düzenleyin.

## 🐛 Sorun Giderme

### Port 5000 Kullanımda
Eğer port 5000 kullanımda ise, `web_agent.py` dosyasındaki port numarasını değiştirin:
```python
socketio.run(app, debug=True, host='0.0.0.0', port=5001)  # Port 5001'e değiştir
```

### Bağımlılık Hataları
```bash
pip install --upgrade pip
pip install -e .
```

### Agent Bağlantı Sorunları
- `fastagent.config.yaml` dosyasının doğru yapılandırıldığından emin olun
- MCP sunucularının çalıştığından emin olun

## 📱 Kullanım

1. Web arayüzü açıldığında, agent otomatik olarak bağlanır
2. Alt kısımdaki metin kutusuna mesajınızı yazın
3. Enter tuşuna basın veya "Send" butonuna tıklayın
4. Agent'ın yanıtını bekleyin
5. Konuşma geçmişi otomatik olarak saklanır

## 🎨 Özelleştirme

### Renk Teması Değiştirme
`templates/index.html` dosyasındaki CSS değişkenlerini düzenleyin:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --accent-color: #4facfe;
}
```

### Agent İsmi Değiştirme
`web_agent.py` dosyasında:
```python
self.fast = FastAgent("Yeni Agent İsmi")
```

## 🔒 Güvenlik

- Web arayüzü sadece yerel ağda çalışır (localhost)
- Üretim ortamında güvenlik önlemleri ekleyin
- HTTPS kullanımı önerilir

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Terminal çıktısını kontrol edin
2. Tarayıcı konsolunu kontrol edin (F12)
3. Agent loglarını kontrol edin (`fastagent.jsonl`)

---

**Not**: Bu web arayüzü, FastAgent'ın terminal tabanlı etkileşimini web tabanlı bir deneyime dönüştürür. Tüm MCP araçları ve agent özellikleri web arayüzünde de kullanılabilir.
