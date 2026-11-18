using System.Text.Json;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);
builder.Logging.SetMinimumLevel(LogLevel.Warning);
builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower);

var connectionString = Environment.GetEnvironmentVariable("DATABASE_URL")
    ?? "Host=localhost;Port=5432;Username=io;Password=io;Database=io;Maximum Pool Size=10";
var dataSource = NpgsqlDataSource.Create(connectionString);

var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapGet("/items", async (int? limit) =>
{
    var n = limit ?? 100;
    if (n < 1 || n > 1000)
        return Results.UnprocessableEntity(new { error = "limit debe estar entre 1 y 1000" });

    await using var cmd = dataSource.CreateCommand(
        "SELECT id, name, price, created_at FROM items ORDER BY id DESC LIMIT $1");
    cmd.Parameters.AddWithValue(n);
    await using var reader = await cmd.ExecuteReaderAsync();

    var items = new List<Item>();
    while (await reader.ReadAsync())
        items.Add(new Item(reader.GetInt32(0), reader.GetString(1), reader.GetDouble(2), reader.GetDateTime(3)));
    return Results.Ok(items);
});

app.MapPost("/items", async (ItemIn input) =>
{
    if (string.IsNullOrEmpty(input.Name) || input.Name.Length > 100 || input.Price < 0)
        return Results.UnprocessableEntity(new { error = "datos invalidos" });

    await using var cmd = dataSource.CreateCommand(
        "INSERT INTO items (name, price) VALUES ($1, $2) RETURNING id, name, price, created_at");
    cmd.Parameters.AddWithValue(input.Name);
    cmd.Parameters.AddWithValue(input.Price);
    await using var reader = await cmd.ExecuteReaderAsync();
    await reader.ReadAsync();

    var item = new Item(reader.GetInt32(0), reader.GetString(1), reader.GetDouble(2), reader.GetDateTime(3));
    return Results.Created($"/items/{item.Id}", item);
});

app.MapGet("/primes", (int? n) =>
{
    var limite = n ?? 20000;
    if (limite < 2 || limite > 200000)
        return Results.UnprocessableEntity(new { error = "n debe estar entre 2 y 200000" });
    return Results.Ok(new { n = limite, count = CountPrimes(limite) });
});

app.Run();

static int CountPrimes(int n)
{
    var count = 0;
    for (var i = 2; i <= n; i++)
    {
        var isPrime = true;
        for (var d = 2; d * d <= i; d++)
        {
            if (i % d == 0)
            {
                isPrime = false;
                break;
            }
        }
        if (isPrime) count++;
    }
    return count;
}

record Item(int Id, string Name, double Price, DateTime CreatedAt);
record ItemIn(string Name, double Price);
