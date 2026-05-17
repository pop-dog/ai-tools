I want to make a script to install global skills into a project. The script should require one argument, the project root. It creates <project            
  root>/.claude/skills (if not exists), symlinks everything from ~/.claude/skills into the project skills folder, and adds those symlinks to the .gitignore 
   file for the project with a comment (create file if not exists)
