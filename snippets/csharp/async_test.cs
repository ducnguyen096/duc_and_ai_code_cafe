// AI helped me write this to understand async behavior in C#
// Not sure if it's optimal — still learning!
using System;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("Starting...");
        await DoWorkAsync();
        Console.WriteLine("Finished!");
    }

    static async Task DoWorkAsync()
    {
        await Task.Delay(1000);
        Console.WriteLine("Working...");
    }
}