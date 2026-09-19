# **GAME DESIGN DOCUMENT (GDD)**

## **CHRONO-CRAFT: Tactical Deck & Physics Execution**

**Disusun Oleh:** Nicholaus

**Target Platform:** PC (Windows) via Python/Pygame  
**Genre:** Deckbuilder, Tactical, Real-Time Physics

**Visual Style:** Retro Cyberpunk / GBA-Style Pixel Art

### **1\. RINGKASAN EKSEKUTIF (ELEVATOR PITCH)**

*Chrono-Craft* adalah game pertarungan taktis yang memadukan strategi penyusunan kartu (*deckbuilding*) dengan eksekusi pertarungan berbasis fisika (*physics-based brawler*). Pemain bertindak sebagai *Chronomancer*, merencanakan serangkaian aksi saat waktu berhenti, lalu mengeksekusinya untuk melihat kekacauan fisika terjadi secara *real-time* di arena.

**Nilai Jual Utama (USP):**

Pemisahan fase *Planning* (Turn-Based) dan *Action* (Real-Time). Pemain tidak hanya memilih serangan, tetapi merancang lintasan (*trajectory*), momentum, dan pentalan layaknya bermain biliar dengan kartu sihir.

### **2\. CORE GAMEPLAY LOOP**

Gameplay dibagi menjadi siklus yang berulang:

1. **Draw Phase:** Pemain mendapatkan 3-5 kartu aksi di tangan.  
2. **Planning Phase (Time Paused):** Pemain men-drag kartu ke "Timeline Slots" (maksimal 3 aksi berurutan). Prediksi lintasan (garis vektor) akan muncul samar-samar di arena untuk menunjukkan arah pergerakan atau tembakan.  
3. **Execution Phase (Real-Time):** Waktu berjalan. Semua aksi dari pemain dan musuh dieksekusi secara otomatis dan berurutan. Mesin fisika (pentalan, benturan, gaya tarik) mengambil alih.  
4. **Resolution Phase:** Waktu kembali berhenti. Damage dihitung dari benturan ke dinding, jebakan arena, atau proyektil.

### **3\. MEKANIK UTAMA & FISIKA (PYGAME)**

* **Vector & Physics System:** Menggunakan pygame.math.Vector2 untuk menghitung pergerakan karakter (X, Y), kecepatan (*Velocity*), dan percepatan (*Acceleration*).  
* **Collision & Bounciness:** Karakter dan objek arena memiliki sifat *bouncy* (memantul). Menabrak dinding atau musuh dengan kecepatan tinggi akan menghasilkan *damage* tambahan (*Kinetic Damage*).  
* **Card Synergy:**  
  * *Kinetic Dash:* Meluncur lurus dengan kecepatan tinggi.  
  * *Repulse/Attract:* Mendorong atau menarik musuh di sekitar menggunakan gaya magnetik buatan.  
  * *Time Dilation:* Memperlambat *Delta Time* (dt) sebesar 50% selama eksekusi.

### **4\. INTEGRASI ARTIFICIAL INTELLIGENCE (AI)**

* **Enemy Heuristic AI:** Musuh tidak bergerak secara acak. AI akan mengevaluasi posisi pemain dan memilih kombinasi kartu dari *deck* musuh yang berpotensi memberikan *damage* pantulan terbesar atau menghindari area berbahaya.  
* **Development Tool (Vibecoding):** Tim akan secara aktif menggunakan Generative AI (LLM seperti GPT-6 Astra) untuk mempercepat pembuatan *boilerplate* Pygame, logika fisika, dan *State Management*.

### **5\. KEBUTUHAN AUDIO & VISUAL**

* **Resolusi:** *Canvas* dasar berukuran rendah (misal ![][image1] piksel) yang di-*scale up* ke layar monitor untuk mempertahankan estetika piksel retro yang tajam (*crisp*).  
* **Art Assets:** Sprite 2D Pixel Art untuk karakter, kartu UI sederhana, dan ubin (*tileset*) arena bergaya lab cyberpunk/neon.  
* **Juiciness / Game Feel:**  
  * *Screen shake* saat terjadi benturan keras.  
  * Partikel piksel saat melakukan *Dash*.  
  * *Hit-stop* (layar berhenti sepersekian detik) saat *damage* besar terjadi untuk memberikan dampak dramatis.

### **6\. RISIKO DAN MITIGASI**

* **Risiko:** Logika UI kartu (*drag & drop*) tumpang tindih dengan logika fisika Pygame.  
* **Mitigasi:** Menerapkan Arsitektur OOP yang ketat. File UI dan File Mesin Fisika dipisah sepenuhnya. State game (PLANNING dan ACTION) tidak boleh berjalan bersamaan.

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFcAAAAZCAYAAABEmrJwAAAE0ElEQVR4Xu2XW2heRRDHT4iKoiheYjSXb79cVJIiRuMFBRWhEStUxFZaahHf6kOp1NIWi0iw9qGKICIotRB80Ac1iA+F3tBCQcQKvthW0KJIMKi0T1WwUOLvnzPbzLc5J/lSU/Xh/GE4u7OzszP/M2d3T5ZVqFChQoX/FL29vVfVarWxrq6uW9Oxnp6eW0IIryK7sFnb3t5+eWrDvMsYXyMb2WpOavNvwMeKbEJu9OPqI+PIo9ZukLa2titKfK1Rjt5Xs2ip1+sv4OAPyBv2A+hWIB8iA52dnV2Mb6B9hIVDtNGLQXcA2a7g8DVE+5jmel8XGhbrOLHd1t3dfT/tb5AzyBPRRvkpT2SqSIh9nfN1TLkoJ9rbkQPKdWbFJoCDe5h4KiTkEmQ7/b0i1Zm3YPcWc0ajAput6I7wvDrq6D+FHJePqLuQ0Dqsd5gYltJtkY5K60f3C/J9X19ft3SML6f/dcir0csh5KDIk63mKIfoX7kpR2R91M0Lq7p3bYEGcu0tf0eQN/k5RuZua08vCtnveRsq5y70p3k+5vUp8H2NJNU7tOKjIzPCyuAq8oR7oSqE90NelcukIM6N9gLOwTj4CP0S9UNeGOlXHH0d8lvHXNCE55EVRlhKbi+6SeQHgnpQOgVCe38kjbEB5GRKrkt2h9en0IvD5hO/zUQMDw9fjJ+XGN+czUOuETSO/ZhPXnGhn1LFqk/7juRlakvcKQ6igvabKReC+ZoUL15fCBK6G+PXLYlZ5IIW+lsUnAU4xgKf0t6kMRlEEsvITfVFwGYI+32e4IUQW4bazKf8a0/JAasiwe4drRd1RmLKRal+FuxN72JCXf0ScoVW9Dsiwcjv2IxkM+RqD9NBcN7kCp7gxSBWwOcqfJzF15aswA9nybWMf4bcG3V2eGn/ncVFs+TqU9De82RUlJCrbWM9tvt53lfPq1YEK+CnZUB72WKQK4hgS1ZnwD8iVi8JHMfnqK9KD8ZWY/NtR0fHdVGnaya6gwVcNEcuBrcH2w6irohc2iNaPJ60WV7FustqL52+CZSRWKafC4on5PvdiVoz+1oJ7Kvcg4/n6Lam44LurIzvxe5juhf5sTISy/QNwOhZDH72wqTTIa/K35DDEHo9z91KtmD+I+hPaRGRQHsyJTGSi2zz+jIYsa8hm5m7hOcevwc3i0gs8azKrPLx8wD9IW8XSg5iG9M2OItEI3ciuZrOj1pB5ZqzWae9nIf8rjjg9igldGm0wc9SdGf09HOL4InNjBBLfkEEyw8xvBHcT4NA/xVdDRPd9HZWlJ8OuZBvfediV26KJ82zKTBpG/KnD8IWOYqzujPVfv0M+g8y+5wIYq1Vf0+0CfkfzZfz/dEYITuRjVmyx4YFEGx+RrH/K/kiJ5Cf9IV5e2zXhfwGtNXrBR10jH8lf1FnPyQT6FY707lhFaatYMrkLPKFtgWGW2v5Vewk8mLIL9e6bO9jkRuiDzvd32bsc/SPh5xYvZSGT7EI2D3E3A1ZyeFlSb08ODh4STrmoS8u5NtQzMNLw9+jEPL7fSG5AoV1J+M/Kn9kpXyoCMoOx/OG3iQLLNciVOLNWTERLRqTjfa4RQ9ikaFbAbGO9Pf3X5mORciGXB5WwbhDvUKFChUqVKhQocL/E38DWo2rhBEDxh8AAAAASUVORK5CYII=>