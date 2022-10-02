There are 2 version of this project.
Ver 1. the 2 python files in the same folder as this readme.txt
Ver 2. the 2 python files in the folder 'With multiprocessing lock - Slower'
       which is in the same folder as this readme.txt


THE DIFFERENCE IS ONLY IN THE CLIENT SIDE.
Ver 2 uses a multiprocessing lock to update a global var that 
contains the number of options that have been checked (in the client side)
and Ver 1 uses a local server that each process communicates with and only the local server updates
the var that contains the number of options that have been checked (in the client side)

in Ver 2 I discovered that the lock causes each process to wait a considerable amount of time,
and that causes a drop in the performance (In Ver 1 when running the client the cpu usage is 100% and 
in Ver 2 when running the client the cpu usage is around 5% to 20% with a maximum of 40%) because all
the processes except 1 are always waiting for that 1 process to release the lock and once he releases
the lock another process acquires it and all the others are waiting, this slows the program,
so I created a new version - Ver 1.