string type                     # "yolo" lub "aruco"
string label                   # Nazwa klasy lub ID znacznika ArUco (jako string)
float32 confidence             # Pewność detekcji (dla YOLO)
geometry_msgs/Point center     # Środek wykrytego obiektu w obrazie
float32 width
float32 height

geometry_msgs/Pose pose        # Szacowana pozycja znacznika względem kamery
float32 distance               # Odległość od kamery (dla znaczników ArUco)
