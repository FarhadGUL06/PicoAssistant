# PicoAssistant

https://ocw.cs.pub.ro/courses/pm/prj2023/danield/gptma


GPT Assistant Speaker este un dispozitiv portabil care preia comenzi din telefon, prin bluetooth și produce răspunsul vocal în 2 limbi posibile (engleză sau română, în funcție de modul selectat). 

Dispune de funcționalități precum: play la piese de pe youtube, vremea din orice oraș în momentul actual sau din următoarele zile, statistici locale de temperatură și umiditate. 

De asemenea, poate face request-uri la ChatGPT, să primească răspunsul și să-l transmită prin boxe.

Scopul acestui proiect este acela de a îndrepta atenția și spre această zonă de proiectare cu microcontrolere, zona de proiectare folosind Cloud, care are la bază API-uri.

In plus, acesta poate prelua date de la un modul ESP32 care transmite date in timp real de oriunde exista o conexiune la internet catre un server local. De la acel server local, 
GPTMA va prelua datele si le va procesa realizand un text mai cursiv. 



# API-uri folosite

ChatGPT

Vreme - https://openweathermap.org/api

Text-to-speech - https://rapidapi.com/voicerss/api/text-to-speech-1

Youtube API - https://github.com/FarhadGUL06/YoutubeAPI

ESP_32_STATS_API - https://github.com/FarhadGUL06/esp32_stats_api 



# Lista comenzi

!ping: se poate verifica conexiunea între telefon și Pico. Se va afișa un „Pong!” pe ecran.

!restart / !reload: se rulează de la început fișierul code.py

!p <payload>: se poate reda piesa cu titlul specificat în <payload>

!tell <payload> / !say <payload>: dispozitivul va transmite audio inputul primit

!mem: memoria RAM disponibilă

!wf <payload>: vremea în viitorul apropiat din orașul dat ca input, dacă <payload> este gol, 
atunci se va analiza vremea în viitorul apropiat din București

!w <payload>: vremea în acest moment din orașul dat ca input, dacă <payload> este gol, 
atunci se va analiza vremea în acest moment din București

!last: se va reda ultimul răspuns primit de la ChatGPT

!lan ro / en: se va seta limba pe ro / en, în funcție de cum este precizat. 
Limba este utilizată și pentru API-ul text-to-speech, selectându-se vocea potrivită limbii selectate

!stats: statistici de temperatură și umiditate din încăperea in care se afla GPT Multimedia Assistant

!esp - statistici de temperatura, umiditate si altele din locul in care se afla ESP32, cu afisare pe ecran

!espv - statistici transmise sub forma audio, prin boxa

<payload>: scriind direct textul, neprefixat de „!”, acesta va fi prelucrat de ChatGPT și se va oferi un 
răspuns
  
  
