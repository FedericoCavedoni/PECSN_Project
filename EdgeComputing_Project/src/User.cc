#include "User.h"
#include "BaseStation.h"

Define_Module(User);

void User::initialize() {
    // Inizializzazione dei parametri
    intervalRate = par("intervalRate");  // Tasso di intervallo per l'invio dei task
    sizeRate = par("sizeRate");          // Tasso per la dimensione del task

    // Verifica se usare una distribuzione uniforme o lognormale per la posizione
    if (par("uniformDistribution").boolValue()) {
        // Distribuzione uniforme
        cModule *parent = getParentModule();
        int width = parent->par("width");  // Larghezza del campo
        int height = parent->par("height");  // Altezza del campo

        // Posizione uniforme nelle coordinate x e y
        x = uniform(0, width, 0);
        y = uniform(0, height, 1);

    } else {
        // Distribuzione lognormale
        int mean = par("mean");          // Media della distribuzione lognormale
        int std_dev = par("std_dev");    // Deviazione standard

        // Posizione lognormale nelle coordinate x e y
        x = lognormal(mean, std_dev, 0);
        y = lognormal(mean, std_dev, 1);
    }

    // Aggiorna la posizione del modulo nel display string
    getDisplayString().setTagArg("p", 0, x);
    getDisplayString().setTagArg("p", 1, y);

    // Invia il primo task dopo un intervallo esponenziale
    cMessage *sendEvent = new cMessage("sendEvent");
    double taskInterval = exponential(intervalRate);  // Calcola l'intervallo per il prossimo task
    scheduleAt(simTime() + taskInterval, sendEvent);  // Pianifica l'invio del task

}

void User::handleMessage(cMessage *msg) {
    // Verifica se il messaggio ricevuto è "sendEvent"
    if (strcmp(msg->getName(), "sendEvent") == 0) {
        // Messaggio di invio di un task
        cPacket *task = new cPacket("Task");

        // Calcola la dimensione del task usando una distribuzione esponenziale
        double taskSize = exponential(sizeRate);
        task->setByteLength(taskSize);  // Imposta la dimensione del task in byte

        // Trova la base station più vicina
        cModule *nearestBaseStation = findNearestBaseStation();

        // Invia il task alla base station più vicina tramite il gate "in"
        sendDirect(task, nearestBaseStation, "in");

        // Pianifica il prossimo invio del task dopo un intervallo esponenziale
        double taskInterval = exponential(intervalRate);
        cMessage *sendEvent = new cMessage("sendEvent");
        scheduleAt(simTime() + taskInterval, sendEvent);  // Pianifica il prossimo "sendEvent"

        // Elimina il messaggio originale
        delete msg;
    } else {
        // Se il messaggio ricevuto non è "sendEvent", logga l'errore
        EV << "Received unknown message: " << msg->getName() << "\n";
        delete msg;  // Elimina il messaggio non riconosciuto
    }
}

cModule *User::findNearestBaseStation() {
    // Trova la base station più vicina all'utente
    cModule *parent = getParentModule();
    int numBaseStations = parent->par("numBaseStations");  // Numero totale di base station
    cModule *nearest = nullptr;
    double minDistance = INFINITY;  // Inizializza la distanza minima come infinita

    // Cicla attraverso tutte le base station per calcolare la distanza
    for (int i = 0; i < numBaseStations; ++i) {
        // Ottieni il modulo della base station
        cModule *baseStation = parent->getSubmodule("baseStations", i);
        BaseStation *bs = check_and_cast<BaseStation *>(baseStation);  // Cast a tipo BaseStation

        // Ottieni le coordinate della base station
        double baseX = bs->get_x();
        double baseY = bs->get_y();

        // Calcola la distanza tra l'utente e la base station
        double distance = std::sqrt(std::pow(baseX - x, 2) + std::pow(baseY - y, 2));

        // Se la distanza è inferiore alla distanza minima trovata, aggiorna la base station più vicina
        if (distance < minDistance) {
            minDistance = distance;
            nearest = baseStation;  // Aggiorna la base station più vicina
        }
    }

    return nearest;  // Ritorna la base station più vicina
}
