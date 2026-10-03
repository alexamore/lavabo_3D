/*
  Fontanella d'angolo - controllo pompa di svuotamento serbatoio
  Scheda: ESP32 DevKit (Arduino core 2.x / 3.x)

  Ingressi:
    GALL_ALTO  (GPIO 32) - galleggiante livello alto  -> avvia la pompa
    GALL_BASSO (GPIO 33) - galleggiante livello basso -> ferma la pompa (protezione marcia a secco)
    I galleggianti sono contatti verso GND, con pull-up interno.
  Uscite:
    POMPA (GPIO 25) - gate MOSFET logic-level (es. IRLZ44N / modulo AO3400), diodo di ricircolo sulla pompa
    LED   (GPIO 2)  - stato: fisso = pompa in marcia, lampeggio lento = ok, lampeggio rapido = guasto

  Logica:
    - livello alto attivo per > DEBOUNCE_MS  -> pompa ON
    - pompa OFF quando il livello basso si libera (+ RUN_ON_MS), oppure dopo MAX_RUN_MS (sicurezza)
    - pausa minima MIN_OFF_MS tra due cicli
    - se il livello alto resta attivo dopo MAX_FAULTS cicli consecutivi a tempo scaduto -> GUASTO
      (pompa bloccata / tubo ostruito): pompa ferma, nuovo tentativo ogni FAULT_RETRY_MS
    - con un solo galleggiante (UN_SOLO_GALLEGGIANTE = true) la pompa gira per TIMED_RUN_MS
*/

#include <Arduino.h>

// ---- configurazione --------------------------------------------------------
const bool UN_SOLO_GALLEGGIANTE = false;
const bool CONTATTO_CHIUSO_CON_ACQUA = true;   // inverti se il galleggiante e' montato capovolto

const int PIN_GALL_ALTO  = 32;
const int PIN_GALL_BASSO = 33;
const int PIN_POMPA      = 25;
const int PIN_LED        = 2;

const uint32_t DEBOUNCE_MS     = 2000;
const uint32_t RUN_ON_MS       = 3000;
const uint32_t MAX_RUN_MS      = 60000;
const uint32_t TIMED_RUN_MS    = 15000;
const uint32_t MIN_OFF_MS      = 10000;
const uint32_t FAULT_RETRY_MS  = 10UL * 60UL * 1000UL;
const int      MAX_FAULTS      = 3;

// ---- stato -----------------------------------------------------------------
enum Stato { ATTESA, MARCIA, RITARDO_STOP, PAUSA, GUASTO };
Stato stato = ATTESA;
uint32_t tStato = 0, tAltoDa = 0, tBassoLiberoDa = 0;
int cicliTimeout = 0;

bool acqua(int pin) {
  bool chiuso = digitalRead(pin) == LOW;
  return CONTATTO_CHIUSO_CON_ACQUA ? chiuso : !chiuso;
}

void pompa(bool on) {
  digitalWrite(PIN_POMPA, on ? HIGH : LOW);
}

void vai(Stato s) {
  stato = s;
  tStato = millis();
  pompa(s == MARCIA || s == RITARDO_STOP);
  static const char* nomi[] = {"ATTESA", "MARCIA", "RITARDO_STOP", "PAUSA", "GUASTO"};
  Serial.printf("[%lu s] stato -> %s\n", millis() / 1000, nomi[s]);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_GALL_ALTO, INPUT_PULLUP);
  pinMode(PIN_GALL_BASSO, INPUT_PULLUP);
  pinMode(PIN_POMPA, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pompa(false);
  vai(ATTESA);
}

void loop() {
  const uint32_t now = millis();
  const bool alto = acqua(PIN_GALL_ALTO);
  const bool basso = UN_SOLO_GALLEGGIANTE ? true : acqua(PIN_GALL_BASSO);

  // debounce livello alto
  if (alto) { if (!tAltoDa) tAltoDa = now; } else tAltoDa = 0;
  const bool altoStabile = tAltoDa && (now - tAltoDa >= DEBOUNCE_MS);

  switch (stato) {
    case ATTESA:
      if (altoStabile && basso) vai(MARCIA);
      break;

    case MARCIA: {
      const uint32_t t = now - tStato;
      if (UN_SOLO_GALLEGGIANTE) {
        if (t >= TIMED_RUN_MS) { cicliTimeout = alto ? cicliTimeout + 1 : 0; vai(cicliTimeout >= MAX_FAULTS ? GUASTO : PAUSA); }
      } else if (!basso) {
        vai(RITARDO_STOP);                       // acqua sotto il livello basso: ancora qualche secondo
      } else if (t >= MAX_RUN_MS) {
        cicliTimeout++;
        vai(cicliTimeout >= MAX_FAULTS ? GUASTO : PAUSA);
      }
      break;
    }

    case RITARDO_STOP:
      if (now - tStato >= RUN_ON_MS) { cicliTimeout = 0; vai(PAUSA); }
      break;

    case PAUSA:
      if (now - tStato >= MIN_OFF_MS) vai(ATTESA);
      break;

    case GUASTO:
      if (now - tStato >= FAULT_RETRY_MS) { cicliTimeout = MAX_FAULTS - 1; vai(ATTESA); }
      break;
  }

  // LED di stato
  bool led;
  if (stato == MARCIA || stato == RITARDO_STOP) led = true;
  else if (stato == GUASTO) led = (now / 150) % 2;
  else led = (now % 2000) < 80;
  digitalWrite(PIN_LED, led);

  delay(20);
}
