#include "ConcreteObserver.h"
#include <iostream>
#include <utility>
#include <vector>
#include "Subject.h"
using namespace std;

ConcreteObserver::ConcreteObserver(string name):
    m_objName(std::move(name)),
    m_observerState(0){
}

#ifdef _WIN32
__declspec(noinline)
#else
__attribute__ ((noinline))
#endif
ConcreteObserver::~ConcreteObserver()= default;

void ConcreteObserver::update(shared_ptr<Subject> sub){
    m_observerState = sub->getState();
    cout << "update oberserver[" << m_objName << "] state:" << m_observerState << endl;
}
