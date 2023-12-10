#include "ConcreteSubject.h"

ConcreteSubject::ConcreteSubject(): m_nState(0){
}

#ifdef _WIN32
__declspec(noinline)
#else
__attribute__ ((noinline))
#endif
ConcreteSubject::~ConcreteSubject()= default;

int ConcreteSubject::getState(){
    return m_nState;
}

void ConcreteSubject::setState(int i){
    m_nState = i;
}
