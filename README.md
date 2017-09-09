# AutoGrader

A Python based AutoGrader for Python Assignments.

## Introduction

This system is developed for [FAST-NUCES Peshawar Campus](http://pwr.nu.edu.pk) for the handling of the student assignments. This system provide auto grading functionality for the students submission and generated submission reports for the Instructor.

### Functionality

1. Admin, Instructor and Student accounts.
2. Course with unique enroll key
3. Assignments with test and assignment file.
4. Assignment Submission Report (based on the latest submission)
5. Student Account: Password Recovery, Submission Password, Submission Score and Submission Log

### Prerequisites

Check [requirement.txt](requirement.txt) for the prerequisites packages. You can install requirment package using following command:
 
```
cd AutoGrader/
pip install -r requirement.txt
```

### Installing

For the installation first grab the latest source from the [GitHub](https://github.com/BilalZaib/AutoGrader)

```
git clone git@github.com:BilalZaib/AutoGrader.git
cd AutoGrader/
```

Edit settings.py of Django

```
cd AutoGr/
mv settings-sample.py settings.py
vi settings.py
cd ../
```
Note: You have to add secret key and SMTP detail in this file. You can generate Django secret key from any online website.

Setting up super user for Django
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Now go to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) to login into the system.

## Getting into system?
1. After the installation admin user will logon to the system.
2. It will create the Instructor, set him as "is_staff" and assign the permissions for example Assignment (All), Course (View only), Student (All) and Submission (All).
3. After the creation of Instructor, instructor will logon to his account.
4. Instructor will create Assignment and share enroll key with students.
5. Student will register to the system from [http://127.0.0.1:8000/autograder](http://127.0.0.1:8000/autograder)
6. Student will logon to the system and enter the enroll key to enroll into the course.
7. Student will select the course, then assignment and then follow the instruction written on that page.

## How system works?
Instructor uploads three files with Assignment which is `assignment_file`, `instructor_test_file` and `student_test_file`. Student will have to write code in `assignment_file` and 
it will be tested against `student_test_file` for student and after the submission to server the `assignment_file` will be tested againts `instructor_test_file` and submission will be stored with score in the database.

## Deployment

Currently this system is used on a dedicated server located in the university with PostgresSQL database. Step for installation are same as the above. 

## Built With

* [Python](http://www.dropwizard.io/1.0.2/docs/) - Language used
* [Django](https://www.djangoproject.com/) - The web framework used

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/BilalZaib/AutoGrader/tags). 

## Authors

* **Hafiz M. Bilal Zaib** - *Initial work* - [BilalZaib](https://github.com/BilalZaib)
* **Mohammad Nauman** - *Design and requirement gathering* - [recluze](https://github.com/recluze)
* **Syed Owais Ali Chishti** - *Funtionality integrations* - [soachishti](https://github.com/soachishti)

See also the list of [contributors](https://github.com/BilalZaib/AutoGrader/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* [autograder-basic](https://github.com/recluze/autograder-basic/) developed by [recluze](https://github.com/recluze) was used for grading purpose.

## Note

There are not sandboxing mechanism in the system, however auto backups and system permission are used for now.