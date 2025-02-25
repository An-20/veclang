#include <iostream>
#include <string>
#include <unordered_map>
#include <sstream>
#include <vector>


struct InterpreterFlags {
    static constexpr bool ENABLE_LOGGING = true;
    static constexpr bool USE_FAST_MATH = false;
};


class Interpreter {
public:
    void interpret(const std::string& code) {
        std::istringstream stream(code);
        std::string line;
        while (std::getline(stream, line)) {
            execute(line);
        }
    }

private:
    std::unordered_map<std::string, int> variables;

    void execute(const std::string& line) {
        std::istringstream stream(line);
        std::string command;
        stream >> command;

        if (command == "print") {
            std::string var;
            stream >> var;
            std::cout << variables[var] << std::endl;
        } else if (command == "set") {
            std::string var;
            int value;
            stream >> var >> value;
            variables[var] = value;
        } else {
            std::cerr << "Unknown command: " << command << std::endl;
        }
    }
};
