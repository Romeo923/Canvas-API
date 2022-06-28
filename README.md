Requires Python >= 3.10

All programs must be run from a subdirectory of the course directory
Course directory must be a subdirectory of the root directory containing inp.json
grades.csv must be in the appropriate course directory

Directory structure (file order within a directory does not matter):
  ROOT
    -> inp.json
    -> CourseID 1
        --> Group 1 (may be empty)
            ---> Files (if any) is to be attatched to group assignments (ex: Homework pdf)
        --> Group 2
        ...
        --> Group N
        
        --> Files 1
            ---> Files not associated with any particular assignment (ex: Slides, Syllabus)
        --> Files 2
        ...
        --> Files N
        
        --> grades.csv
        
        --> Possibly other unrelated folders
    -> CourseID 2
    ...
    -> CourseID N
    
    -> Possibly other unrelated related forlders
    
inp.json structure:
  login_token : token,
  Default : default setings,
  CourseID : course settings and default overrides

Default Settings : 
  Assignments : {
      Group 1 : group settings,
      Group 2 : group settings,
      ...
      Group N : group settings
  },
  Files : {
      FileSet 1 : file settings,
      FileSet 2 : file settings,
      ...
      FileSet N : file settings,
  },
  Tabs : ordered list of visible tabs,
  Class_Schedule : {
      days : list of days class occurs (ex: [Mon, Wed, Fri]),
      holy_days : list of specific dates class does not occur formatted mm/dd/yyyy
  }
  
Course Settings;
  IDs : dictionary of assignment, file, and group ids,
  Default overrides
