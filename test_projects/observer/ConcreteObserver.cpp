#include "ConcreteObserver.h"
#include <iostream>
#include <utility>
#include <vector>
#include "Subject.h"
using namespace std;

ConcreteObserver::ConcreteObserver(string name):
    m_objName(std::move(name)),
    m_observerState(0)
{
}

#pragma optimize("", off)
ConcreteObserver::~ConcreteObserver()
{
}
#pragma optimize("", on)

void ConcreteObserver::update(shared_ptr<Subject> sub)
{
    m_observerState = sub->getState();
    cout << "update oberserver[" << m_objName << "] state:" << m_observerState << endl;
}
