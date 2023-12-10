#pragma once
#include "Observer.h"
#include <string>
#include <memory>
using namespace std;

class ConcreteObserver : public Observer
{

public:
    ConcreteObserver(string name);
    ~ConcreteObserver();
    virtual void update(shared_ptr<Subject> sub);

private:
    string m_objName;
    int m_observerState;
};
