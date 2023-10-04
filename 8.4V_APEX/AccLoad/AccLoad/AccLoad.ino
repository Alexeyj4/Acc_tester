#define numOfSlots 8
#define array_len 20 //array length for measure filter
#define valid_threshold 230 //not valid measure filter value
#define valid_check_flag 1 //check measure valid or not chech

const int Upin[]={54,56,58,60,62,64,66,68};
const int Ipin[]={55,57,59,61,63,65,67,69};

const float Ucal[]={44.34,  44.34,  44.34,  44.34, 44.34,  44.34, 44.34, 44.34}; //U measure calibration array //U(volts)=U(ADC)/Ucal
const float Ical[]={310.5,  310.5,  310.5,  310.5,  310.5,  310.5,  310.5,  310.5}; //I measure calibration array //I(amperes)=I(ADC)/Ical

int Umeas;
int Imeas;
int u[numOfSlots][array_len];
int i[numOfSlots][array_len];

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  for(int s=0;s<numOfSlots;s++)  
  {
    pinMode(Upin[s],INPUT);
    pinMode(Ipin[s],INPUT);
  }

analogReference(INTERNAL1V1);
}


float toVolts(int s) //count average and converting
{ 
  float sum=0;
  for(int a=0;a<array_len;a++){
    sum+=u[s][a];
  }
  return float(sum)/float(array_len)/Ucal[s];
}

float toAmperes(int s) //count average and converting
{
  float sum=0;
  for(int a=0;a<array_len;a++){
    sum+=i[s][a];
  }
  return float(sum)/float(array_len)/Ical[s];
}

int valid(int s){  //s=slot number 
  if(valid_check_flag==0)return 1;
  int umin=1024;
  int umax=0;
  int imin=1024;
  int imax=0;
  for(int a=0;a<array_len;a++){
    if(umin>u[s][a])umin=u[s][a];
    if(umax<u[s][a])umax=u[s][a];
    if(imin>i[s][a])imin=i[s][a];
    if(imax<i[s][a])imax=i[s][a];
  }
  if((umax-umin)>valid_threshold){
    //Serial.println("nv"); //debug
    return 0;
  }
  if((imax-imin)>valid_threshold){
    //Serial.println("nv"); //debug
    return 0;
  }
  return 1;
}

void loop() {
  // put your main code here, to run repeatedly:
    
  for(int a=0;a<array_len;a++){
    for(int s=0;s<numOfSlots;s++){
      u[s][a]=analogRead(Upin[s]);
      i[s][a]=analogRead(Ipin[s]);      
    }
  }
   for(int s=0;s<numOfSlots;s++){
      if(valid(s)==1){
        Serial.println("slot");
        Serial.println(s);
        Serial.println(toVolts(s));
        Serial.println(toAmperes(s));       
      }      
   }
 
  delay(100);
}
