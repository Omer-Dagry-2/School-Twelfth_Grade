files, lock, threads & processes are created using Windows api

I've created a class for Threads and for Processes
I've implemented almost everything, I ran into sum problems with
when implementing the Process class, I had to think of a way to transfer
the args and kwargs and to think of a way to even call the function,
because unlike the 'beginthreadex' the 'CreateProcess' doesn't take a
function as a parameter, it takes a command that runs in cmd (or another app if you want)
so I had to somehow call the desired function and I wanted to do it dynamically, not
just specific to this project, so it tool sum thinking and researching

