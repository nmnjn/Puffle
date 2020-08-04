# Puffle

Puffle is a python application to automatically connect to the Microsoft Teams Meetings according to your timetable.

# Getting started 📦

### Download the source code from [here](https://github.com/nmnjn/Puffle/archive/master.zip) and navigate to the project directory.

## Step 1: Editing the configuration 👨🏻‍💻

`config.json` has the following values. Fill them up correctly as they are the lifeline of the system.

- email → this is the email with which you will log into MS teams.
- password → this is the password to your account. (Don't worry, the password is safe as it is only kept on your device as long as the application is running)
- email-notification → set this as `true` to get a **mail** when Puffle joins your meetings. It is recommended to keep this as `true` so that you're also informed in case Puffle gets an error and is not able to join the meeting.
- p-email → this is your primary email on which you will receive the alerts from Puffle.
- phone-notification → set this as `true` to get a **text message** when Puffle joins your meetings. By default, this is set to `false` and it is only available to subscribed users. More about this later.
- phone → the phone number you would like to receive the text messages on.

```json
//example config.json

{
  "email": "naman.jain5@learner.manipal.edu",
  "password": "********",

  "email-notification": true,
  "p-email": "naman17@gmail.com",
  "phone-notification": true,
  "phone": "963****503"
}
```

---

## Step 2: Editing the timetable 📝

`timetable.json` has the following structure. Fill it up as accurately as possible.

```json
{
    "Day": [
        {
            "team": "",
            "channel": "",
            "time": "",
            "duration": 100
        }
    ]
  }
```

- The timetable is divided into days of the week.
- Each day has a list of meetings to join.
- Each meeting has the following properties:
    - team → this is the name of the team from MS Teams. ***(needs to match exactly)***
    - channel → this is the channel which has the meeting. ***(needs to match exactly)***
    - time → this is the time of the day when you want to join the meeting. (follow the 24 hour format i.e 6pm = "18:00", 6am = "06:00". Make sure to put 0 if the hour is less than 10.)
    - duration → this is the duration of the meeting, specified in the number of minutes. leave this as 0 if you do not want the meeting to end after a certain time.

- Few important things to note:
    - Make sure your json is properly formatted. Use an online tool to verify.
    - The `team`, `channel`, and `time` are put in double quotes. The `duration` is an integer value.

```json
//example timetable.json

{
    "Monday": [
        {
            "team": "EOM 7th sem CSE A and B (Essentials of Management, HUM 4001)",
            "channel": "General",
            "time": "17:00",
            "duration": 100
        }
    ],
    "Tuesday": [
        {
            "team": "PCAP: SEM 6",
            "channel": "General",
            "time": "12:00",
            "duration": 120
        }
    ],
    "Wednesday": [
        {
            "team": "Starship",
            "channel": "V",
            "time": "20:05",
            "duration": 100
        },
        {
            "team": "ADG",
            "channel": "General",
            "time": "22:00",
            "duration": 10
        }
    ],
    "Thursday": [
        {
            "team": "Testing",
            "channel": "General",
            "time": "10:29",
            "duration": 5
        },
        {
            "team": "EEFM",
            "channel": "General",
            "time": "14:00",
            "duration": 100
        }
    ],
    "Friday": [
        {
            "team": "2017 - 2018 MBBS 2nd",
            "channel": "ENT and Head and Neck Surgery",
            "time": "11:30",
            "duration": 60
        }
    ],
    "Saturday": [
        {
            "team": "2017 - 2018 MBBS 2nd",
            "channel": "ENT and Head and Neck Surgery",
            "time": "11:30",
            "duration": 60
        }
    ]
  }
```

## Step 3: Running the Application 🤙🏻

After you have successfully edited and verified the `config.json` and `timetable.json` , you can continue to run the application. 

### Method 1

- Set up a local Python3 virtual environment
- Install the requirements : `pip install -r requirements.txt`
- Run the application by `python app.py`

### Method 2

For some easy usage, I have compiled the binaries for each operating system.

You can find them in the release folder or download them from here:

- MacOS [(Download Here)](https://github.com/nmnjn/Puffle/raw/master/release/puffle_macos_v1.1.zip)
- Linux [(Download Here)](https://github.com/nmnjn/Puffle/raw/master/release/puffle_linux_v1.1.zip)
- Windows (Coming Soon)

After you have downloaded the zip file, unzip and navigate to the directory using the command line. Here you will find two items:

1. The application binary.
2. A configs folder which will contain your information and timetable (like the above steps).

In a unix environment, navigate to the project directory from the command line.

1. Give the execution permission by running `chmod +x app`.
2. Then run the application by `./app`

Voila ✨

**Puffle** is written in Python3. If you have a python environment installed and know your way around the command line, feel free to check out the source code [here](https://github.com/nmnjn/Puffle) and give it a star 🌟.

This project is heavily inspired from [Teams-Auto-Joiner by TobiasPankner.](https://github.com/TobiasPankner/Teams-Auto-Joiner)

---

# Text Message Subscription 🤝

If you would like to receive alerts and updates on your phone, [please reach out to me](mailto:naman17@gmail.com) and we can set up a subscription for you. I wanted to make this product accessible and free for everyone to use, however bearing the cost of sending so many messages will burn through my savings :p

Alternatively I have set up a system to send a mail to your primary account, which does not have any cost associated to it. 

---

# Troubleshooting 🛠

Meh, I expected you to come here. Even though I tried my best, this is not a perfect product.

Here are some solutions to the common problems you may face.

> **I was not able to find any teams!
If *Teams* is in grid mode, please change it to list mode.**

The very first time you ran the application and it printed this in the console.

By default teams opens in grid mode the first time it is launched. I was unable to find a way around this, so you will have to manually help me out. 

- **Click on the gear icon** near the top right corner of the screen next to the *join or create team* button.
- Select **Switch view.**
- Click on the **List Layout**.
- Restart the application.

> **Unexpected slowdowns and timeouts**

If you are using your laptop while Puffle starts to connect you to a meeting, let it complete its process first, and then you can get back to your work. 

Puffle opens a chrome web browser and works by actively reading what is on the screen. Switching windows while its connecting can lead to slowdowns and timeout. 

> **Windows Support**

Puffle works on windows just as smooth as any other operating system, However, I do not have a windows machine to test and develop on, and I did not want to push out some broken code without testing. 

If you have a strong heart and know your way around python feel free to check out the source code and run it with the steps above. 

I am working to get this on windows as fast as possible. 

---

# Important 🚨

This is just a fun weekend project and I do not expect it to work 100%. I built this to ease my life. 

I would also like to state that this is just to showcase the extent of some automation capability with Python. I *do not* condone blowing off your classes and will not be responsible for any repercussions you face.

**In case you miss any classes, due to some error in setting up the system or the application not performing as intended, I will not be responsible for it.**
