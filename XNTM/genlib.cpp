#include "json.hpp"
#include <algorithm>
#include <fstream>
#include <ios>
#include <iostream>
#include <iterator>
#include <map>
#include <sstream>
#include <string.h>
#include <string>
#include <typeinfo>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>
#include <chrono>

using json = nlohmann::json;
using namespace std;

vector<string> Mixer = {"6h", "6v", "4"};
vector<string> Module = {"6h", "6v", "4", "r1", "r2", "r3", "r4", "r5"};
const int GridSize = 7;

pair<int, int> Msize(string Mname) {
  vector<pair<int, int>> size = {{2, 3}, {3, 2}, {2, 2}};
  int i = 0;
  for (auto itr = Mixer.begin(); itr != Mixer.end(); itr++) {
    if (Mname == *itr) {
      return size[i];
    }
  }
  if (Mname[0] == 'r') {
    string digi = Mname.substr(1, Mname.size() - 1);
    int v = stoi(digi);
    return make_pair(v, 1);
  } else
    cerr << "error in Msize()" << endl;
  return make_pair(0, 0);
}

int MCellNum(string Mname) {
  pair<int, int> S = Msize(Mname);
  int v = 1;
  v *= S.first;
  v *= S.second;
  return v;
}

vector<vector<int>> gengrid(string M) {
  vector<vector<int>> grid(GridSize, vector<int>(GridSize, -1));
  pair<int, int> start = make_pair(2, 2);
  pair<int, int> size = Msize(M);
  for (int i = 0; i < size.first; i++) {
    for (int j = 0; j < size.second; j++) {
      int ni = i + start.first;
      int nj = j + start.second;
      grid[ni][nj] = 0;
    }
  }
  return grid;
}

void showgrid(vector<vector<int>> grid) {
  for (int i = 0; i < GridSize; i++) {
    for (int j = 0; j < GridSize; j++) {
      cout << setw(2) << grid[i][j];
    }
    cout << endl;
  }
}

string getModule(string ModuleName) {
  vector<string> FirstChar = {"6", "4", "r"};
  for (int i = 0; i < 3; i++) {
    if (FirstChar[i] == ModuleName.substr(0, 1))
      return FirstChar[i];
  }
  return "0";
}

bool HasKey(string key, json object) {
  auto itr_check = object.find(key);
  if (itr_check != object.end())
    return true;
  else
    return false;
}

bool SameArray(json array, json cmp_array) {
  if (array.size() == cmp_array.size()) {
    for (int i = 0; i < array.size(); i++) {
      if (array[i] != cmp_array[i])
        return false;
    }
    return true;
  }
  return false;
}

void PrintArray(json array) {
  cout << "[";
  for (int i = 0; i < array.size(); i++) {
    cout << array[i] << ",";
  }
  cout << "]" << endl;
}

bool ArrayContainsValue(json value, json Array) {
  for (auto v : Array) {
    if (v == value) {
      return true;
    }
  }
  return false;
}

int main() {
  auto start = chrono::system_clock::now(); 

  ifstream reading1("XNTM/data/PlacementChild.json", ios::in);
  json placementChild;
  reading1 >> placementChild;

  ifstream reading2("XNTM/data/prov_ratio.json", ios::in);
  json prov_ratio;
  reading2 >> prov_ratio;

  ifstream reading3("XNTM/data/PlacementProvDrops.json", ios::in);
  json placementProvDrops;
  reading3 >> placementProvDrops;

  json lib;
  for (string PM : Mixer) {
    lib[PM] = json::object();
    auto now = chrono::system_clock::now(); 
    auto diff = chrono::duration_cast<chrono::hours>(now-start).count(); 
    cout<<"PM:"<<PM<<"の処理に取り掛かる.ここまでの経過時間:"<<diff<<"分"<<endl; 
    for (auto ratio : prov_ratio[PM]) {
      now = chrono::system_clock::now(); 
      diff = chrono::duration_cast<chrono::hours>(now-start).count();
      cout<<"PM:"<<PM<<",ratio:"<<ratio<<"の処理開始.ここまでの経過時間:"<<diff<<"分"<<endl; 
      unordered_map<string,unordered_set<json> > data_set;
      string s_ratio = ratio.dump(); 
      lib[PM][s_ratio] = json::object();

      for (auto Combo : placementProvDrops[PM][s_ratio]) {
        do {
          json buffer;
          for (int i = 0; i < Combo.size() + 1; i++)
            buffer[to_string(i)] = json::array();
          json initial_value = {{"Module",
                                 {{"6", json::array()},
                                  {"4", json::array()},
                                  {"r", json::array()}}},
                                {"CannotPlace", json::array()},
                                {"Layer", gengrid(PM)}};
          buffer[to_string(0)].push_back(initial_value);
          for (int idx = 0; idx < Combo.size(); idx++) {
            json DropsLeftByAModule = Combo[idx];
            for (auto buff : buffer[to_string(idx)]) {
              for (string MODULE : Module) {
                string DropLeftNum = to_string(DropsLeftByAModule.size());
                if (placementChild[PM][MODULE].contains(DropLeftNum)) {
                  for (auto candidate :
                       placementChild[PM][MODULE][DropLeftNum]) {
                    if (SameArray(candidate["overlapping_cell"],
                                  DropsLeftByAModule)) {
                      bool passing = true;
                      json check_cells = candidate["flushing_cell"];
                      for (auto check_cell : check_cells) {
                        if (ArrayContainsValue(check_cell,
                                               buff["CannotPlace"])) {
                          passing = false;
                        }
                      }
                      if (passing) {
                        json new_buff = buff;
                        int layer = 1;
                        json layer_search_cells = candidate["flushing_cell"];
                        for (auto item : candidate["overlapping_cell"])
                          layer_search_cells.push_back(item);
                        for (auto layer_search_cell : layer_search_cells) {
                          int y = layer_search_cell[0];
                          int x = layer_search_cell[1];
                          layer = max(layer, int(buff["Layer"][y][x]) + 1);
                        }
                        for (auto layer_search_cell : layer_search_cells) {
                          int y = layer_search_cell[0];
                          int x = layer_search_cell[1];
                          new_buff["Layer"][y][x] = layer;
                        }
                        for (auto item : candidate["overlapping_cell"]) {
                          new_buff["CannotPlace"].push_back(item);
                        }
                        json AddedModule = candidate;
                        AddedModule["layer"] = layer;
                        if (getModule(MODULE) == "6") {
                          AddedModule["orientation"] = MODULE.substr(1, 1);
                        }
                        string ModuleKind = MODULE.substr(0, 1);
                        new_buff["Module"][ModuleKind]
                            .get_ref<json::array_t &>()
                            .push_back(AddedModule);
                        buffer[to_string(idx + 1)] += new_buff;
                      }
                    }
                  }
                }
              }
            }
          }
          if (!buffer[to_string(Combo.size())].empty()) {
            for (auto data : buffer[to_string(Combo.size())]) {
              vector<int> modulecnt(3, 0);
              vector<string> leftnumPerModule(3, "");
              vector<string> ModuleFirstC = {"6", "4", "r"};
              for (int i = 0; i < ModuleFirstC.size(); i++) {
                modulecnt[i] += int(data["Module"][ModuleFirstC[i]].size());
                // 各モジュールごとにソート(値は，prov_cellの先頭のセル)
                vector<pair<int, json>> v(MCellNum(PM),
                                          make_pair(-1, json::object()));
                for (auto obj : data["Module"][ModuleFirstC[i]]) {
                  json cmp = obj["overlapping_cell"][0];
                  int left_num = obj["overlapping_cell"].size();

                  int y = cmp[0], x = cmp[1];
                  y -= 2;
                  x -= 2;
                  if (getModule(PM) == "6") {
                    if (PM.substr(1, 1) == "h") {
                      v[3 * y + x] = make_pair(left_num, obj);
                    } else {
                      v[2 * y + x] = make_pair(left_num, obj);
                    }
                  } else {
                    v[2 * y + x] = make_pair(left_num, obj);
                  }
                  leftnumPerModule[i] += to_string(left_num);
                }
                json new_array = json::array();
                for (int j = 0; j < MCellNum(PM); j++) {
                  if (v[j].first > 0) {
                    new_array.get_ref<json::array_t &>().push_back(v[j].second);
                  }
                }
                data["Module"][ModuleFirstC[i]] = new_array;
                sort(leftnumPerModule[i].begin(), leftnumPerModule[i].end(),
                     [](char c1, char c2) { return c1 > c2; });
              }
              data.erase(data.find("Layer"));
              data.erase(data.find("CannotPlace"));
              // libに詰め込むときのキー値のひとつとなる各モジュールの数を表す文字列の生成
              string key = "[";
              for (int i = 0; i < ModuleFirstC.size(); i++) {
                key += "[";
                key += to_string(modulecnt[i]);
                key += ",[";
                key += leftnumPerModule[i];
                key += "]],";
              }
              key = key.substr(0, key.size() - 1) + "]";
              if (!lib[PM][s_ratio].contains(key))
                lib[PM][s_ratio][key] = json::array();
              if (!data_set.contains(key))
                  data_set.emplace(key,unordered_set<json>()); 
              if (!data_set[key].contains(data)) {
                data_set[key].emplace(data);
                lib[PM][s_ratio][key].get_ref<json::array_t &>().push_back(data);
              }
            }
          }
          else{
              cout<<"warning:ユニークな配置法が見つからなかった.Comboの順列あり."<<endl; 
          }
        } while (next_permutation(Combo.begin(), Combo.end()));
      }
      ofstream writing_file;
      string WriteFileName = "XNTM/data/lib"+PM+s_ratio+".json"; 
      now = chrono::system_clock::now(); 
      diff = chrono::duration_cast<chrono::hours>(now-start).count();
      cout<<WriteFileName<<"の書き出し.ここまでの経過時間:"<<diff<<"分"<<endl; 
      writing_file.open(WriteFileName,ios::out); 
      writing_file << lib[PM][s_ratio] <<endl; 
      writing_file.close(); 
    }
  }
      ofstream writing_file; 
      string WriteFileName = "XNTM/data/lib.json"; 
      writing_file.open(WriteFileName,ios::out); 
      writing_file << lib <<endl; 
      writing_file.close();
      auto now = chrono::system_clock::now(); 
      auto diff = chrono::duration_cast<chrono::hours>(now-start).count();
      cout<<"genlib処理終了.ここまでの経過時間:"<<diff<<"分"<<endl;
      return 0;
}
