#ifndef USER_H
#define USER_H

#include <omnetpp.h>

using namespace omnetpp;

class User : public cSimpleModule {
  private:
    double x;
    double y;

    double taskInterval;
    double taskSize;

    double intervalRate;
    double sizeRate;

    cMessage *sendEvent;
    cModule *nearestBaseStation;
    cGate *destGate;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    cModule *findNearestBaseStation();
};

#endif // USER_H
