
public class Truck
{
    public void Deliver()
    {
        Console.WriteLine("Truck delivery");
    }
}

public class Ship
{
    public void Deliver()
    {
        Console.WriteLine("Ship delivery");
    }
}

public class LogisticsApp
{
    public void PlanDelivery(string transportType)
    {
        if (transportType == "Truck")
        {
            Truck truck = new Truck();
            truck.Deliver();
        }
        else if (transportType == "Ship")
        {
            Ship ship = new Ship();
            ship.Deliver();
        }
    }
}

public interface ITransport //Product - загальний інтерфейс для об'єктів 
{
    void Deliver();
}

public class PatternTruck : ITransport //ConcreteProduct - конкретний продукт
{
    public void Deliver()
    {
        Console.WriteLine("Pattern Truck delivery");
    }
}

public class PatternShip : ITransport //ConcreteProduct - конкретний продукт
{
    public void Deliver()
    {
        Console.WriteLine("Pattern Ship delivery");
    }
}

public abstract class Logistics //Creator - базовий клас, що містить фабричний метод
{
    public abstract ITransport CreateTransport(); //фабричний метод
    public void PatternPlanDelivery() // базова логіка з використанням фабричного методу
    {
        ITransport transport = CreateTransport();
        transport.Deliver();
    }
}

public class RoadLogistics : Logistics //ConcreteCreator - конкретний творець
{
    public override ITransport CreateTransport()
    {
        return new PatternTruck();
    }
}
public class SeaLogistics : Logistics //ConcreteCreator - конкретний творець
{
    public override ITransport CreateTransport()
    {
        return new PatternShip();
    }
}

class Program
{
    static void Main(string[] args)
    {
        
        Logistics roadLogistics = new RoadLogistics();
        roadLogistics.PatternPlanDelivery();
        
        Logistics seaLogistics = new SeaLogistics();
        seaLogistics.PatternPlanDelivery();

    }
}
