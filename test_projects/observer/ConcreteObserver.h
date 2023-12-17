#pragma once
#include "Observer.h"
#include <string>
#include <memory>

class ConcreteObserver : public Observer
{

public:
    ConcreteObserver(std::string name);
    ~ConcreteObserver();
    virtual void update(std::shared_ptr<Subject> sub);

private:
    std::string m_objName;
    int m_observerState;
};
