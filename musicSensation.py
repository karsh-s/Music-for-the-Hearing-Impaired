#Importing all required modules
import mido
from mido import MidiFile
from mido import Message, MidiTrack
import RPi.GPIO as gpio
import time
import threading

#Disable any motor warning
gpio.setwarnings(False)

#Functions below initialises all motors that are connected to the Raspberry Pi
def initialiseMelodyMotors():
    #The mode is set so the numbers correspond with the GPIO value
    gpio.setmode(gpio.BCM)
    gpio.setup(17,gpio.OUT)
    gpio.setup(22,gpio.OUT)

#The function above is repeated for the bass motors
def initialiseBassMotors():
    gpio.setmode(gpio.BCM)
    gpio.setup(23,gpio.OUT)
    gpio.setup(24,gpio.OUT)

#This function turns on the melody motors
#The parameters are duration and intensity
def vibrateMelodyMotor(duration, intensity):
    #By declaring this motor, the intensity can be controlled
    motorOne = gpio.PWM(17, 1000)
    #Vibrate motor at set intensity
    motorOne.ChangeDutyCycle(intensity)
    motorOne.start(intensity)
    gpio.output(22,False)
    #Vibrate motors for specific duration
    time.sleep(duration)

#This function turns on the bass motors
#The parameters are duration and intensity
def vibrateBassMotor(duration, intensity):
    #By declaring this motor, the intentisity can be controlled
    motorTwo = gpio.PWM(23,1000)
    #Vibrate motor at set intensity
    motorTwo.ChangeDutyCycle(intensity)
    motorTwo.start(intensity)
    gpio.output(24,False)
    #Vibrate motors for specifc duration
    time.sleep(duration)

#This function stops the melody motors only
def stopMelodyMotor():
    gpio.output(22,False)
    gpio.cleanup()
    time.sleep(0.2)

#This function stops the bass motors only
def stopBassMotor():
    gpio.output(23,False)
    gpio.output(24,False)
    gpio.cleanup()
    time.sleep(0.2)

#This function detects the notes from a song
#Paraneter is a list
def detectNotes(noteList):
    #Set list of all possible notes that can be recognised
    musicNote= ['A', 'A# or Bb', 'B', 'C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B', 'C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B','C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B', 'C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B', 'C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B', 'C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B', 'C','C# or Db', 'D', 'D# or Eb', 'E', 'F', 'F# or Gb', 'G', 'G# or Ab', 'A', 'A# or Bb', 'B', 'C']

    #List is created to store the song's notes
    songNotes= []

    #For each of the notes in the list, it uses the notenumber finds the note equivalent of it
    for notes in noteList:
        notes -= 21
        songNotes.append(musicNote[notes])

    #A list of all the song's notes are returned
    return songNotes

#This function reads MIDI files and Vibrates Motors based on it
#Parameters for this function include file of the song, melody track, lowest note, presence of bass, and bass track
def readMidiFileAndPlaySong(song, track, lowestNote, bass, bassTrack):

    #Open MIDI File to dissect
    importedSongFile = mido.MidiFile(song, clip = True)

    #Find the ticks per beat
    ticksPerBeat = importedSongFile.ticks_per_beat

    #The tempo of the song is found by locating metamessages of the "set_tempo" type on the first track
    for basicSettings in importedSongFile.tracks[0]:
        if basicSettings.is_meta and basicSettings.type == "set_tempo":
            songTempo = basicSettings.tempo

    #Lists for notes, duration and velocity are created for both bass and melody
    melodyNoteNumber = []
    bassNoteNumber = []
    melodyVelocity=[]
    bassVelocity = []
    melodyNoteDurationInSeconds = []
    bassNoteDurationInSeconds= []
    repeat = 0

    #If the parameters given shows that there is a bass, the MIDI file will be read through twice. One time for melody and the other time for bass
    #Otherwise, the MIDI file will be only read through once for the melody
    if bass == True:
        numberOfRepeats = 2
    else:
        numberOfRepeats = 1

    #This 'for' loop finds the velocity, notenumebr and duration in seconds
    for repeat in range(numberOfRepeats):

        #Basic lists for the loop
        noteNumber = []
        velocity = []
        noteDuration = []
        noteDurationInSeconds = []
        messageNumber = -1
        nextNote = 1
        collectivetime = 0

        repeat += 1

        #On the second repition, the bass track will be dissected instead of the melody track
        if repeat == 2:
            track = bassTrack
            lowestNote = 0

        #Each of the messages in the selected track are examined and dissected
        for message in importedSongFile.tracks[track]:

            #This variable helps find an exact message when referring to it since it keeps track of what message is being examined
            messageNumber +=1

            #If the message is a metamessage, it is ignored since it does not contain any valuable data
            if message.is_meta:
                pass

            #If it isn't a metamessage, it checks if the message type is "note_on" or "note_off"
            else:
                if message.type == "note_on" or message.type == "note_off":

                    #If the message type is "note_on" or "note_off", the message is checked to make sure it belongs to either the melody or base and the message is an instruction to play a note
                    #If the velocity is 0, it means the message is turning off a note, so the code checks that the velocity is greater than 0
                    if message.note >= lowestNote and message.velocity > 0:

                        #If the message is detected to turn on a note, the notenumber and velocity is added to a list
                        noteNumber.append(importedSongFile.tracks[track][messageNumber].note)
                        velocity.append(importedSongFile.tracks[track][messageNumber].velocity)

                        #For each of the messages that turn on a note, the next message which is composed of the same notenumber but has a velocity of 0 is located
                        while True:
                            try:
                                if importedSongFile.tracks[track][messageNumber+nextNote].note == importedSongFile.tracks[track][messageNumber].note and importedSongFile.tracks[track][messageNumber+nextNote].velocity == 0:

                                    #Once the message to turn off the note is located, the collective time between the two messaged is calculated and that is the note duration
                                    collectivetime = collectivetime + importedSongFile.tracks[track][messageNumber+nextNote].time
                                    noteDuration.append(collectivetime)
                                    nextNote = 1
                                    collectivetime = 0
                                    break

                                else:

                                    #If the message doesn't turn off the note, the time is added to the collective time since it means that the note would be playing whilst this message is occurring.
                                    collectivetime += importedSongFile.tracks[track][messageNumber+nextNote].time
                                    nextNote += 1
                            except:
                                nextNote +=1

        #For each of the notes and their durations, the durations are converted from ticks to seconds
        #The durations are initially gathered as ticks
        for lengthOfTime in noteDuration:
            try:
                baseValue = songTempo * 1e-6 / ticksPerBeat
            except:
                songTempo = 500000
                baseValue = songTempo * 1e-6 / ticksPerBeat

            #Append the note durations in seconds to another list
            lengthOfTime = round(lengthOfTime * baseValue,2)
            noteDurationInSeconds.append(lengthOfTime)

        #If the first repition occurred, the list values are placed in the melody list values
        if repeat == 1:
            melodyNoteNumber = noteNumber
            melodyVelocity = velocity
            melodyNoteDurationInSeconds = noteDurationInSeconds

        #If the second repition occurred, the list values are palced in the bass list values
        elif repeat == 2:
            bassNoteNumber = noteNumber
            bassVelocity = velocity
            bassNoteDurationInSeconds = noteDurationInSeconds

    #This function is created inside the parent function so the melody and bass are played simultaneously
    def playMelody():
        playCounter = 0

        #The note detection function is called and the list of melody note numbers is inputted to fullfill the parameters
        translatedNotes = detectNotes(melodyNoteNumber)

        #For each note, the motor is vibrating
        while playCounter < len(melodyNoteDurationInSeconds):

            #The melody motor need to initialise before running
            initialiseMelodyMotors()

            #The note that the melody plays is printed on the screen. Example: "Melody: C"
            print("Melody:", translatedNotes[playCounter])
            playCounter += 1

            #The melody motor vibrates for a set duration (the note duration) and to a set intensity (the note velocity)
            vibrateMelodyMotor(melodyNoteDurationInSeconds[playCounter-1], melodyVelocity[playCounter-1])

            #The melody motor is stopped
            stopMelodyMotor()
            time.sleep(0.2)

    #This function is created inside the parent function so the melody and bass are played simultaneously
    def playBass():
        bassCounter = 0

        #The note detection function is called and the list of melody note numebrs is inputted to fullfill the parameters
        translatedBassNotes = detectNotes(bassNoteNumber)

        #For each note, the bass motor vibrates
        while bassCounter < len(bassNoteDurationInSeconds):

            #The bass motor needs to initialise before running
            initialiseBassMotors()

            #The note that the melody plays is printed on the screen. Example: "Bass: G"
            print("Bass:", translatedBassNotes[bassCounter])
            bassCounter +=1

            #The bass motor vibrates for a set duration (chord duration) and to a set intensity (chord velocity)
            vibrateBassMotor(bassNoteDurationInSeconds[bassCounter-1], bassVelocity[bassCounter-1])

            #The bass motor is stopped
            stopBassMotor()
            time.sleep(0.2)

    #The two functions are added to a thread so they can function simultaneously
    firstThread = threading.Thread(target = playMelody)
    secondThread = threading.Thread(target = playBass)

    #The melody function and bass function vibrate simultaneously playing their corresponding notes
    firstThread.start()
    secondThread.start()

#The user input is requested. The user has to select a song to play
chooseSong = input("Please select a song from the following: \n 1. Happy Birthday \n 2. My Heart Will Go On From the Titanic\n 3. Fly Me to The Moon \n")

#If Happy Birthday is chosen, only a melody is played through the motors
if chooseSong == "1" or chooseSong == "Happy Birthday" or chooseSong ==  "happy birthday":
    print("Happy Birthday has been chosen")
    time.sleep(2)
    readMidiFileAndPlaySong('HappyBirthday.mid', 1, 60, False,1)

#If My Heart Will Go On is chosen, the melody and bass are played through the motors
elif chooseSong == "2" or chooseSong == "Titanic" or chooseSong == "titanic" or chooseSong == "my heart will go on" or chooseSong == "My Heart Will Go On" or "My Heart Will Go On From the Titanic" or chooseSong == "my heart will go on from the titanic":
    print("My Heart Will Go On has been chosen")
    time.sleep(2)
    readMidiFileAndPlaySong('Titanic-Heart.mid', 0, 55, True, 1)

#If Fly Me To The Moon is chosen, the melody and bass are played through the motors
elif chooseSong == "Fly Me To The Moon" or chooseSong =="3" or chooseSong =="fly me to the moon":
    print("Fly Me To The Moon has been chosen")
    time.sleep(2)
    readMidiFileAndPlaySong('FlyMeToTheMoon.mid',1,0, True, 0)

#If the user input was faulty, an error will be printed
else:
    print("ERROR | Input was invalid")
