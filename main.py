# Creator: Israel Showell
# Start Date: 8-24-24
# End Date: 8-24-24
# Project: AI Transcriber Project
# Version: 1.00

# Description: 
"""
This project is a GUI AI transcriber that allows a user to transcribe Youtube videos using AI!
This script uses Python libraries such as Pytubefix, Tkinter, FFMpeg, os, and math to handle logic, and faster_whisper is used to 
manage the AI transcriptions!
"""

#These are the necessary imports for the script
import tkinter as tk #GUI interface
from tkinter import messagebox as messagebox #For file dialogs
import ffmpeg as ffm #ffmpeg wrapper for Python
import os #For file operations
import pytubefix as pytube #For downloading the YouTube videos
from faster_whisper import WhisperModel #For transcribing the audio
import math #For rounding numbers

#def retrieveURL():

#We use ffmpeg to extract audio from the video,
#But pytubefix has a built-in method to get the audio, which may be more efficient
def extract_audio(input_file):
    print(f"Extracting audio from {input_file}...")
    
    #Sets the extracted audio file name to be "audio-input_file.wav"
    extracted_audio = f"audio-{input_file}.wav"
    
    try:
        #This extracts the audio and saves it to the specified file
        ffm.input(input_file).output(extracted_audio).run(overwrite_output=True)
    except ffm.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        print(f"FFmpeg error: {error_message}")
        raise e
    
    # Returns the name of the audio file
    return extracted_audio


#This function transcribes the audio file using OpenAI's open source Whisper model
def transcribe_audio(audio):
    #Creates a Whisper model with a small size on CPU
    #The smaller the size, the less memory usage, and the less accurate the transcription will be
    model = WhisperModel("small", device="cpu")
    
    #From the faster-whisper Github repository
    """
    Warning: segments is a generator so the transcription only starts when you iterate over it. 
    The transcription can be run to completion by gathering the segments in a list or a for loop:
    """
    segments, info = model.transcribe(audio)
    
    #This us what language the audio is in
    language = info[0]
    
    #This is where we transcribe each segment
    segments = list(segments)
    
    #This loop will print out each segment with its start and end time and the transcribed text.
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

    return language, segments
 

#This helper function preprocesses the subtitles into the (SRT) format
#It takes times in seconds and converts them into HH:MM:SS,sss format
def convert_to_SRT(seconds):
    #SubRip(SRT) format
    #Subtitle index: 0, 1, 2, etc
    #Timecode: Start and end markers. HH:MM:SS,sss format
    #Text: The subtitle text
    
    #The seconds value is rounded down to the nearest whole number using math.floor(). 
    seconds = math.floor(seconds)
    
    #The number of hours is calculated by dividing seconds by 3600 (# of seconds in an hour) using integer division (//).
    hours = seconds // 3600
    
    #The total number of seconds is then reduced by the equivalent seconds in those hours (3600 * hours). 
    #This leaves the remaining seconds after the hours have been accounted for.
    seconds = seconds - (3600 * hours)
    
    #The number of minutes is calculated by dividing the remaining seconds by 60 (# of seconds in a minute) using integer division (//).
    minutes = seconds // 60
    
    #The total number of seconds is further reduced by the equivalent seconds in those minutes (60 * minutes). 
    #This leaves the remaining seconds after both hours and minutes have been accounted for.
    seconds = seconds - 60 * minutes
    
    #This function then returns a formatted string representing the time in HH:MM:SS,sss format:
    return f"{hours:02}:{minutes:02}:{seconds:02},000"
       
#This function generates the subtitle file in SRT format
def generate_subtitle_file(input_file, language, segments):
    # The function takes three parameters:
    # 'input_file' - the name/path of the input media file
    # 'language' - the language code for the subtitles (e.g., 'en' for English)
    # 'segments' - a list of segment objects containing start time, end time, and text for each subtitle
    
    #Creates the subtitle file name by formatting it as 'sub-input_file.language.srt'
    subtitle_file = f"sub-{input_file}.{language}.srt"

    #Initializes an empty string 'text' that will hold all subtitle entries
    text = ""

    # Iterates over each segment in the 'segments' list with an index
    # 'index' will start from 0, each 'segment' contains start time, end time, and text
    for index, segment in enumerate(segments):

        #Formats the start time of the segment using the 'format_time_for_srt' function
        #Converts the start time into 'HH:MM:SS,mmm' needed for SRT files
        segment_start = convert_to_SRT(segment.start)
        
        #Formats the end time of the segment similarly
        segment_end = convert_to_SRT(segment.end)
      
        #Adds the subtitle sequence number to 'text' (SRT numbering starts from 1)
        text += f"{str(index + 1)}\n"
        
        #Adds the timecode line indicating start and end times separated by '-->'
        text += f"{segment_start} --> {segment_end}\n"
        
        #Adds the subtitle text/content
        #The two newline characters separate the next subtitle entry
        text += f"{segment.text}\n\n"
                
        #Debugging statements
        print(f"Segment {index + 1}:")
        print(f"Start: {segment_start}, End: {segment_end}, Text: {segment.text}")
        
    # Opens a new file with the name 'subtitle_file' in write mode ('w')
    f = open(subtitle_file, "w")

    #Writes the accumulated subtitle text to the file
    f.write(text)

    #Closes the file to ensure all data is properly saved
    f.close()
    
    #Returns the name/path of the generated subtitle file
    return subtitle_file

#This function adds the generated subtitle file to the video file using ffmpeg

def add_subtitle_to_video(input_file, subtitle_file, subtitle_language):
    
    #Set the output video file name to be "output-input_file-subtitle_language.mp4
    output_video = f"output-{input_file}-{subtitle_language}.mp4"
    
    try:
        #Tries to apply the subtitle filter to the video
        ffm.input(input_file).output(output_video, vf=f"subtitles={subtitle_file}").run(overwrite_output=True)
        
    except ffm.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        print(f"FFmpeg error: {error_message}")
        raise e


#This function retrieves the YouTube video URL from the user input
def getURL():
    
    #Gets the user's text stored in the text area
    url = URL_entry.get() 
    
    #This protects against an empty URL string
    if not url:
        messagebox.showwarning("Input Error", "Please enter a valid YouTube URL.")
        return
    
    #Debugging statement
    print(url)
    
    try:
        #Creates a pytubefix instance
        yt_video = pytube.YouTube(url)
        
        #Downloads the highest resolution mp4 video after ordering by resolution
        stream = yt_video.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        #If the video stream is found, download it to the user's directory
        if stream:
 
            #Defines the working directory
            working_directory = os.getcwd()
            
            #Downloads the video to the working directory
            stream.download(output_path=working_directory)
            
            #This gets the file name
            video_file = stream.default_filename
            
            #This removes the mp4 video extension for easier manipulation
            video_title = video_file#.replace(".mp4", "")
            #os.rename(os.path.join(working_directory, video_file), os.path.join(working_directory, f"{video_title}.mp4"))
            
            #Debugging statement
            print("Video downloaded successfully!")

            #The below statements handle the process the video for transcription
            print(video_title)
            #Saves the result of the function into this variable
            audio_extract = extract_audio(video_title)
            print("Audio extracted successfully!")
            
            #Saves the language and segments into these variables
            language, segments = transcribe_audio(audio_extract)
            print("Language and segments retrived successfully!")
            
            #Subtitle file is generated by this function call
            subtitle_file = generate_subtitle_file(video_title, language, segments)
            print("Subtitle file made successfully!")
            
            #Adds the generated subtitle file to the video using this function call
            add_subtitle_to_video(video_title, subtitle_file, language)
            print("Subtitles added successfully!")
            
            #Notifies the user that the transcription and subtitle process completed successfully
            messagebox.showinfo("Success", "Transcription and subtitle process completed successfully!")
        else:
            messagebox.showwarning("Download Error", "No video stream found for download.")
        
    except pytube.exceptions.PytubeFixError as e:
        messagebox.showwarning("Pytube Error", f"An error occurred with Pytube: {e}")
        print(f"Pytube Error: {e}")
    
    except Exception as e:
        messagebox.showwarning("An error occurred", f"{e}")
        print(f"An error occurred: {e}")
    
    finally:
        messagebox.showinfo("Thank You", "Thanks for using AI Transcriber! ")


# Creates the main window
root = tk.Tk()
root.title("AI Transcriber")  #Sets the window title
root.geometry("500x500")  #Sets the window size to 500x500 pixels

# Creates input fields and labels
URL_label = tk.Label(root, text="Enter your Youtube Video's URL:")  # Creates the label
URL_label.pack(pady=10)  #Packs the label into the window with padding
URL_entry = tk.Entry(root)  #Creates an input field to enter the URL
URL_entry.pack(pady=10)  #Packs the input field into the window with padding

# Creates a button that calls the function
run_button = tk.Button(root, text="Transcribe Video!", command=getURL)
run_button.pack(pady=20)  #Packs the button into the window with padding

#Runs the main event loop of the application
root.mainloop()

#Debugging statements since pytube wasn't working properly

# import pytubefix as pytube

# # Print the path to the pytubefix installation
# print("Pytubefix is installed at:", pytubefix.__file__)

# # Locate the innertube.py file in the pytubefix directory
# import os
# pytubefix_dir = os.path.dirname(pytubefix.__file__)
# innertube_path = os.path.join(pytubefix_dir, 'innertube.py')

# print("Innertube.py path:", innertube_path)
