There are 2 version of this project.
Ver 1. the one in the same folder as this readme.txt
Ver 2. the one in the folder 'With multiprocessing lock - Slower' which is in the same folder as this readme.txt


the difference is only in the client side.
Ver 2 uses a multiprocessing lock to update a global var that 
contains the number of options that have been checked (in the client side)
and Ver 1 uses a local server that each process cummunicates with and only the local server updates
the var that contains the number of options that have been checked (in the client side)

in Ver 2 I discovered that the lock causes each process to wait a considerable amount of time,
and that causes a drop in the performance (In Ver 1 when running the client the cpu usage is 100% and 
in Ver 2 when running the client the cpu usage is 40% to 60%) because each all the processes except 1 are 
always waiting for that 1 process to release the lock and once he releases the lock another process acquires
it and all the others are waiting. this slows the program so I created a knew version - Ver 1.
